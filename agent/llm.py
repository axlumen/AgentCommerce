"""
LLM 客户端管理

提供带缓存的 LLM 实例，避免每次调用重复初始化。
"""

import functools
import logging

from config import AGENT_MODEL, AGENT_TOOL_TIMEOUT

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_llm():
    """获取 LLM 客户端（缓存单例）"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=AGENT_MODEL,
        temperature=0.3,
        timeout=AGENT_TOOL_TIMEOUT,
    )


def get_llm_with_tools():
    """获取绑定了工具的 LLM"""
    from agent.tools import TOOL_LIST

    llm = get_llm()
    return llm.bind_tools(TOOL_LIST)
