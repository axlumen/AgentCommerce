"""
Agent 核心图

基于 LangGraph StateGraph 构建 ReAct 循环：
  START → agent_node → [有工具调用?]
                          ├─ 是 → human_node → [需确认?]
                          │         ├─ 是 → interrupt → 等待确认
                          │         │         恢复后 → tool_node → agent_node
                          │         └─ 否 → tool_node → agent_node
                          └─ 否 → END

特性：
- ReAct 推理模式：思考 → 行动 → 观察 → 再思考
- 敏感操作 human-in-the-loop 确认
- 错误处理与超时机制
- 工具调用审计记录
"""

import json
import logging
import time
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from agent.llm import get_llm_with_tools
from agent.memory import memory_manager
from agent.prompts import SYSTEM_PROMPT, build_confirmation_message, format_preferences
from agent.security import (
    check_tool_permission,
    requires_confirmation,
    validate_tool_args,
)
from agent.state import AgentState
from agent.tools import TOOLS_BY_NAME
from config import AGENT_MAX_ITERATIONS, AGENT_MAX_TOOL_WORKERS, AGENT_MODEL

logger = logging.getLogger(__name__)


# ============================================================
# Graph 节点
# ============================================================


def agent_node(state: AgentState) -> dict:
    """
    Agent 节点：调用 LLM 决定下一步行动

    ReAct 模式中的"思考"阶段。
    集成：熔断器保护 + AI 调用日志 + 决策追踪。
    """
    from monitoring.circuit_breaker import CircuitOpenError, ai_circuit_breaker
    from monitoring.logger import AICallLog, AgentTrace, log_ai_call, log_agent_trace

    messages = state["messages"]
    step = sum(1 for m in messages if isinstance(m, AIMessage))

    # 构建完整的消息列表（system + 对话历史）
    full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    # 添加用户偏好上下文
    user_prefs = state.get("user_preferences", {})
    if user_prefs:
        pref_text = format_preferences(user_prefs)
        full_messages.insert(1, SystemMessage(content=f"用户偏好信息：{pref_text}"))

    start_time = time.time()

    try:
        # 通过熔断器调用 LLM
        def _call_llm():
            llm_with_tools = get_llm_with_tools()
            return llm_with_tools.invoke(full_messages)

        response = ai_circuit_breaker.call(_call_llm)
        elapsed_ms = (time.time() - start_time) * 1000

        # 记录 AI 调用日志
        input_preview = messages[-1].content[:200] if messages and hasattr(messages[-1], "content") else ""
        output_preview = response.content[:200] if response.content else ""
        log_ai_call(AICallLog(
            model=AGENT_MODEL,
            latency_ms=elapsed_ms,
            success=True,
            input_preview=input_preview,
            output_preview=output_preview,
            call_type="llm",
            user_id=state.get("user_id"),
            session_id=state.get("session_id"),
        ))

        # 记录决策追踪
        log_agent_trace(AgentTrace(
            session_id=state.get("session_id", ""),
            user_id=state.get("user_id"),
            step=step,
            node="agent_node",
            thought=response.content[:200] if response.content else "",
            latency_ms=elapsed_ms,
            success=True,
        ))

        return {"messages": [response]}

    except CircuitOpenError:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning("LLM circuit breaker OPEN, returning fallback")
        log_ai_call(AICallLog(model=AGENT_MODEL, latency_ms=elapsed_ms, success=False, error="circuit_open", call_type="llm"))
        error_msg = AIMessage(content="抱歉，AI 服务暂时繁忙，请稍后再试。")
        return {"messages": [error_msg]}

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.exception("LLM call failed", extra={"session_id": state.get("session_id")})
        log_ai_call(AICallLog(model=AGENT_MODEL, latency_ms=elapsed_ms, success=False, error=str(e), call_type="llm"))
        log_agent_trace(AgentTrace(
            session_id=state.get("session_id", ""), step=step, node="agent_node",
            latency_ms=elapsed_ms, success=False, error=str(e),
        ))
        # 用户侧只返回通用提示，详细异常已在日志中
        error_msg = AIMessage(content="抱歉，AI 服务暂时不可用，请稍后再试。")
        return {"messages": [error_msg]}


def human_node(state: AgentState) -> dict:
    """
    人工确认节点：检查敏感工具调用，通过 interrupt 暂停等待用户确认。

    执行逻辑：
    1. 首次执行：发现敏感工具 → interrupt() 暂停 → 返回占位更新
    2. 恢复执行：interrupt() 返回用户响应 → 处理确认/拒绝
    """
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {}

    confirmed_actions = set(state.get("confirmed_actions", set()))

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]

        if not requires_confirmation(tool_name):
            continue

        action_key = f"{tool_name}:{tool_call['id']}"

        if action_key in confirmed_actions:
            continue

        # 构建确认信息
        args = tool_call["args"]
        confirm_info = build_confirmation_message(tool_name, args)

        # interrupt 暂停，等待用户确认
        user_response = interrupt({
            "action": tool_name,
            "tool_call_id": tool_call["id"],
            "args": args,
            "message": confirm_info,
        })

        # 处理用户响应
        if user_response and user_response.get("approved"):
            confirmed_actions.add(action_key)
        else:
            # 用户拒绝：注入拒绝消息
            reject_msg = ToolMessage(
                content=json.dumps({
                    "rejected": True,
                    "message": "用户已取消此操作",
                }, ensure_ascii=False),
                tool_call_id=tool_call["id"],
            )
            return {
                "messages": [reject_msg],
                "confirmed_actions": confirmed_actions,
            }

    return {"confirmed_actions": confirmed_actions}


def tool_node(state: AgentState) -> dict:
    """
    工具执行节点：并行执行工具调用

    ReAct 模式中的"行动 + 观察"阶段。
    使用 ThreadPoolExecutor 并行执行多个工具，contextvars 复制上下文。
    """
    import contextvars
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from monitoring.logger import AgentTrace, log_agent_trace

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {}

    step = sum(1 for m in state["messages"] if isinstance(m, AIMessage))
    start_time = time.time()
    tool_calls = list(last_message.tool_calls)

    def _run_single_tool(tool_call):
        """在线程中执行单个工具（带上下文复制）"""
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        tool_start = time.time()

        # 安全校验
        if not check_tool_permission(tool_name):
            return tool_call_id, ToolMessage(
                content=json.dumps({"error": f"没有权限调用 {tool_name}"}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            ), False, "permission_denied"

        # 参数校验
        try:
            validated_args = validate_tool_args(tool_name, tool_args)
        except ValueError as e:
            return tool_call_id, ToolMessage(
                content=json.dumps({"error": str(e)}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            ), False, str(e)

        # 执行工具
        tool = TOOLS_BY_NAME.get(tool_name)
        if not tool:
            return tool_call_id, ToolMessage(
                content=json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            ), False, "unknown_tool"

        try:
            result = tool.invoke(validated_args)
            elapsed = (time.time() - tool_start) * 1000
            return tool_call_id, ToolMessage(content=str(result), tool_call_id=tool_call_id), True, elapsed
        except TimeoutError:
            return tool_call_id, ToolMessage(
                content=json.dumps({"error": f"工具 {tool_name} 执行超时"}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            ), False, "timeout"
        except Exception as e:
            logger.exception(f"Tool {tool_name} execution failed")
            return tool_call_id, ToolMessage(
                content=json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            ), False, str(e)

    # 并行执行：为每个线程复制独立的 contextvars 副本
    results_by_id = {}

    with ThreadPoolExecutor(max_workers=min(len(tool_calls), AGENT_MAX_TOOL_WORKERS)) as executor:
        futures = {
            executor.submit(contextvars.copy_context().run, _run_single_tool, tc): tc
            for tc in tool_calls
        }
        for future in as_completed(futures):
            tool_call_id, msg, success, detail = future.result()
            results_by_id[tool_call_id] = (msg, success, detail)

    # 按原始顺序收集结果 + 记录追踪
    results = []
    for tc in tool_calls:
        tc_id = tc["id"]
        if tc_id in results_by_id:
            msg, success, detail = results_by_id[tc_id]
            results.append(msg)

            # 记录决策追踪
            log_agent_trace(AgentTrace(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id"),
                step=step,
                node="tool_node",
                tool_name=tc["name"],
                tool_args=tc["args"],
                tool_result=msg.content[:200] if success else "",
                latency_ms=detail if success else 0,
                success=success,
                error="" if success else str(detail),
            ))

    total_elapsed = (time.time() - start_time) * 1000
    logger.info(f"Tool node: {len(results)} tools in {total_elapsed:.0f}ms (parallel)")

    return {"messages": results}


# ============================================================
# 条件边
# ============================================================


def should_continue(state: AgentState) -> Literal["human_node", "__end__"]:
    """
    判断是否继续执行工具调用

    - 最后一条消息有 tool_calls → 继续到 human_node
    - 否则 → 结束
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 检查迭代次数限制
    tool_calls_count = sum(
        1 for m in messages if isinstance(m, AIMessage) and m.tool_calls
    )
    if tool_calls_count >= AGENT_MAX_ITERATIONS:
        logger.warning(f"Max iterations ({AGENT_MAX_ITERATIONS}) reached")
        return "__end__"

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "human_node"

    return "__end__"


def after_human(state: AgentState) -> Literal["tool_node", "agent_node", "__end__"]:
    """
    人工确认后判断

    - 如果有被拒绝的工具调用 → 回到 agent_node 让 LLM 重新规划
    - 否则 → tool_node 执行工具
    """
    last_message = state["messages"][-1]

    # 如果产生了拒绝消息，回到 agent_node
    if isinstance(last_message, ToolMessage):
        try:
            content = json.loads(last_message.content)
            if content.get("rejected"):
                return "agent_node"
        except (json.JSONDecodeError, TypeError):
            pass

    return "tool_node"


# ============================================================
# 图构建
# ============================================================


def build_agent_graph():
    """
    构建 Agent 图

    流程：
    START → agent_node → should_continue?
                            ├─ human_node → after_human?
                            │                  ├─ tool_node → agent_node (循环)
                            │                  └─ agent_node (用户拒绝，重新规划)
                            └─ END
    """
    builder = StateGraph(AgentState)

    # 添加节点
    builder.add_node("agent_node", agent_node)
    builder.add_node("human_node", human_node)
    builder.add_node("tool_node", tool_node)

    # 添加边
    builder.add_edge(START, "agent_node")
    builder.add_conditional_edges("agent_node", should_continue, ["human_node", END])
    builder.add_conditional_edges("human_node", after_human, ["tool_node", "agent_node"])
    builder.add_edge("tool_node", "agent_node")

    # 编译（使用内存 checkpointer 支持 interrupt）
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


# 全局单例
_agent_graph = None


def get_agent_graph():
    """获取 Agent 图单例"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_agent_graph()
    return _agent_graph
