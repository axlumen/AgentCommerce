"""
Agent API 路由

提供智能导购 Agent 的 HTTP 接口：
- POST /api/agent/chat          — Agent 对话（主入口）
- POST /api/agent/confirm       — 确认敏感操作
- GET  /api/agent/history/{session_id}  — 获取对话历史
- DELETE /api/agent/history/{session_id} — 清除对话历史
- GET  /api/agent/preferences   — 获取用户偏好
"""

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langgraph.types import Command

from agent.graph import get_agent_graph
from agent.memory import memory_manager
from agent.security import detect_injection, sanitize_input
from agent.tools import set_request_context, reset_request_context, get_tool_call_log, clear_tool_call_log
from database import get_db
from dependencies import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI 智能导购 Agent"])


# ============================================================
# 请求/响应模型
# ============================================================


class ChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: str | None = Field(None, description="会话 ID（为空则自动创建）")


class ChatResponse(BaseModel):
    """Agent 对话响应"""
    reply: str = Field(..., description="Agent 回复")
    session_id: str = Field(..., description="会话 ID")
    tool_calls: list[dict] = Field(default_factory=list, description="工具调用记录")
    needs_confirm: bool = Field(False, description="是否需要用户确认")
    confirm_action: str | None = Field(None, description="待确认的操作名")
    confirm_args: dict | None = Field(None, description="待确认的操作参数")
    confirm_message: str | None = Field(None, description="确认提示消息")


class ConfirmRequest(BaseModel):
    """确认操作请求"""
    session_id: str = Field(..., description="会话 ID")
    approved: bool = Field(..., description="是否确认")
    thread_id: str | None = Field(None, description="线程 ID（用于 resume interrupt）")


class PreferencesResponse(BaseModel):
    """用户偏好响应"""
    user_id: int
    preferences: dict


# ============================================================
# API 端点
# ============================================================


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Agent 对话主入口

    发送消息给智能导购 Agent，Agent 会：
    1. 分析用户意图
    2. 调用合适的工具（搜索、查详情、校验库存等）
    3. 基于工具结果生成回复

    集成：限流检查、语义缓存、监控。
    敏感操作（如加购）会返回 needs_confirm=True，前端需引导用户确认。
    """
    # 限流检查
    from monitoring.rate_limiter import rate_limiter
    from config import RATE_LIMIT_PER_MINUTE

    allowed, rate_info = rate_limiter.check(
        f"user:{current_user.id}",
        limit=RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请 {rate_info.get('reset_at', 60)} 秒后重试",
        )

    # 安全检查
    if detect_injection(request.message):
        raise HTTPException(status_code=400, detail="输入包含不安全内容")

    message = sanitize_input(request.message)
    session_id = request.session_id or str(uuid.uuid4())
    thread_id = f"user_{current_user.id}_{session_id}"

    # 加载用户偏好
    user_prefs = memory_manager.get_user_preferences(current_user.id)

    # 加载短期记忆
    history = memory_manager.get_short_term(session_id)

    # 构建消息列表
    messages = [HumanMessage(content=message)]

    # 获取 Agent 图
    agent_graph = get_agent_graph()

    # 配置（thread_id 用于 checkpointer）
    config = {"configurable": {"thread_id": thread_id}}

    # 初始状态
    initial_state = {
        "messages": messages,
        "user_id": current_user.id,
        "session_id": session_id,
        "tool_call_history": [],
        "confirmed_actions": set(),
        "user_preferences": user_prefs,
        "context_window_size": 20,
        "pending_confirmation": None,
    }

    try:
        # 设置请求上下文（工具执行时使用）
        clear_tool_call_log()
        db_token = set_request_context(db, current_user.id)

        try:
            # 执行 Agent
            result = agent_graph.invoke(initial_state, config=config)
        finally:
            reset_request_context(db_token)

        # 处理 interrupt（需要确认的情况）
        snapshot = agent_graph.get_state(config)
        if snapshot and snapshot.next:
            # 有未完成的节点 → 存在 interrupt
            interrupt_value = None
            if snapshot.tasks:
                for task in snapshot.tasks:
                    if hasattr(task, "interrupts") and task.interrupts:
                        interrupt_value = task.interrupts[0].value
                        break

            if interrupt_value:
                return ChatResponse(
                    reply=interrupt_value.get("message", "需要您的确认"),
                    session_id=session_id,
                    tool_calls=_extract_tool_calls(result),
                    needs_confirm=True,
                    confirm_action=interrupt_value.get("action"),
                    confirm_args=interrupt_value.get("args"),
                    confirm_message=interrupt_value.get("message"),
                )

        # 正常回复
        reply = _extract_reply(result)
        tool_calls = _extract_tool_calls(result)

        # 保存短期记忆
        updated_messages = result.get("messages", [])
        msg_dicts = _messages_to_dicts(updated_messages)
        memory_manager.save_short_term(session_id, msg_dicts)

        # 异步更新用户偏好（不阻塞响应）
        try:
            new_prefs = memory_manager.extract_preferences_from_messages(msg_dicts)
            if new_prefs:
                memory_manager.update_user_preferences(current_user.id, new_prefs)
        except Exception:
            pass  # 偏好更新失败不影响主流程

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            tool_calls=tool_calls,
            needs_confirm=False,
        )

    except Exception as e:
        logger.exception("Agent execution failed")
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@router.post("/confirm", response_model=ChatResponse)
async def agent_confirm(
    request: ConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    确认敏感操作

    当 Agent 返回 needs_confirm=True 时，前端调用此接口确认或取消。
    """
    session_id = request.session_id
    thread_id = request.thread_id or f"user_{current_user.id}_{session_id}"

    agent_graph = get_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # 设置请求上下文
        clear_tool_call_log()
        db_token = set_request_context(db, current_user.id)

        try:
            # 使用 Command resume 恢复执行
            resume_command = Command(resume={"approved": request.approved})
            result = agent_graph.invoke(resume_command, config=config)
        finally:
            reset_request_context(db_token)

        reply = _extract_reply(result)
        tool_calls = _extract_tool_calls(result)

        # 检查是否还有新的 interrupt
        snapshot = agent_graph.get_state(config)
        needs_confirm = False
        confirm_action = None
        confirm_args = None
        confirm_message = None

        if snapshot and snapshot.next:
            for task in (snapshot.tasks or []):
                if hasattr(task, "interrupts") and task.interrupts:
                    interrupt_value = task.interrupts[0].value
                    needs_confirm = True
                    confirm_action = interrupt_value.get("action")
                    confirm_args = interrupt_value.get("args")
                    confirm_message = interrupt_value.get("message")
                    break

        # 保存记忆
        updated_messages = result.get("messages", [])
        msg_dicts = _messages_to_dicts(updated_messages)
        memory_manager.save_short_term(session_id, msg_dicts)

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            tool_calls=tool_calls,
            needs_confirm=needs_confirm,
            confirm_action=confirm_action,
            confirm_args=confirm_args,
            confirm_message=confirm_message,
        )

    except Exception as e:
        logger.exception("Confirm action failed")
        raise HTTPException(status_code=500, detail=f"确认操作失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取对话历史"""
    messages = memory_manager.get_short_term(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """清除对话历史"""
    memory_manager.clear_short_term(session_id)
    return {"session_id": session_id, "cleared": True}


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
):
    """获取用户偏好"""
    prefs = memory_manager.get_user_preferences(current_user.id)
    return PreferencesResponse(user_id=current_user.id, preferences=prefs)


@router.get("/stats")
async def agent_stats(current_user: User = Depends(get_current_user)):
    """获取 Agent 调用统计（含缓存、熔断器状态）"""
    stats = {}
    try:
        from monitoring.logger import get_stats
        stats = get_stats()
    except Exception as e:
        logger.debug(f"Failed to get AI stats: {e}")

    cache_stats = {}
    try:
        from cache.semantic_cache import semantic_cache
        cache_stats = semantic_cache.stats()
    except Exception as e:
        logger.debug(f"Failed to get cache stats: {e}")

    circuit_info = {}
    try:
        from monitoring.circuit_breaker import ai_circuit_breaker
        circuit_info = ai_circuit_breaker.get_info()
    except Exception as e:
        logger.debug(f"Failed to get circuit breaker info: {e}")

    return {
        "ai_stats": stats,
        "cache": cache_stats,
        "circuit_breaker": circuit_info,
    }


# ============================================================
# 辅助函数
# ============================================================


def _extract_reply(result: dict) -> str:
    """从 Agent 结果中提取回复文本"""
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return msg.content
    return "抱歉，我暂时无法生成回复。"


def _extract_tool_calls(result: dict) -> list[dict]:
    """从 Agent 结果中提取工具调用记录"""
    tool_calls = []
    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "tool": tc["name"],
                    "args": tc["args"],
                })
        elif isinstance(msg, ToolMessage):
            try:
                content = json.loads(msg.content)
                # 找到对应的 tool call
                for tc in reversed(tool_calls):
                    if "result" not in tc:
                        tc["result"] = content
                        break
            except (json.JSONDecodeError, TypeError):
                pass
    return tool_calls


def _messages_to_dicts(messages: list) -> list[dict]:
    """将 LangChain 消息列表转为字典列表（用于存储）"""
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            if msg.content:
                result.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            result.append({"role": "tool", "content": msg.content})
    return result
