"""
Agent 状态定义

使用 TypedDict 定义 LangGraph Agent 的共享状态，
包含对话历史、工具调用记录、用户偏好等。
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent 共享状态"""

    # 对话历史：使用 add_messages reducer 自动追加消息
    messages: Annotated[list[AnyMessage], add_messages]

    # 当前用户 ID（由路由层注入）
    user_id: int | None

    # 当前会话 ID
    session_id: str

    # 工具调用记录：审计和调试用
    # [{"tool": str, "args": dict, "result": str, "timestamp": float, "duration_ms": float}]
    tool_call_history: list[dict]

    # 已确认的动作 ID 集合（配合 human-in-the-loop）
    confirmed_actions: set[str]

    # 长期记忆：用户偏好（从 Redis 加载）
    user_preferences: dict

    # 滑动窗口大小
    context_window_size: int

    # 当前待确认的工具调用
    pending_confirmation: dict | None
