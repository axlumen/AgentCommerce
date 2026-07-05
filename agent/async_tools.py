"""
异步工具执行器

职责：
- 并行执行多个工具调用（asyncio.gather）
- 异步 LLM 调用（langchain_openai async API）
- 超时控制
"""

import asyncio
import json
import logging
import time
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

logger = logging.getLogger(__name__)


async def execute_tools_parallel(
    tool_calls: list[dict],
    tools_by_name: dict,
    db=None,
    user_id: int | None = None,
    timeout: float = 30.0,
) -> list[ToolMessage]:
    """
    并行执行多个工具调用

    Args:
        tool_calls: 工具调用列表 [{"name": str, "args": dict, "id": str}, ...]
        tools_by_name: 工具名称→工具函数映射
        db: 数据库会话
        user_id: 用户 ID
        timeout: 单个工具超时（秒）

    Returns:
        ToolMessage 列表
    """
    if not tool_calls:
        return []

    # 设置请求上下文
    from agent.tools import set_request_context, reset_request_context
    db_token = set_request_context(db, user_id)

    try:
        # 创建并行任务
        tasks = []
        for tc in tool_calls:
            task = _execute_single_tool(tc, tools_by_name, timeout)
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 构建 ToolMessage 列表
        messages = []
        for i, result in enumerate(results):
            tc = tool_calls[i]
            if isinstance(result, Exception):
                messages.append(ToolMessage(
                    content=json.dumps({"error": str(result)}, ensure_ascii=False),
                    tool_call_id=tc["id"],
                ))
            else:
                messages.append(result)

        return messages

    finally:
        reset_request_context(db_token)


async def _execute_single_tool(
    tool_call: dict,
    tools_by_name: dict,
    timeout: float,
) -> ToolMessage:
    """
    执行单个工具调用（带超时）

    Args:
        tool_call: {"name": str, "args": dict, "id": str}
        tools_by_name: 工具映射
        timeout: 超时秒数

    Returns:
        ToolMessage
    """
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_call_id = tool_call["id"]

    tool = tools_by_name.get(tool_name)
    if not tool:
        return ToolMessage(
            content=json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False),
            tool_call_id=tool_call_id,
        )

    # 参数校验
    from agent.security import validate_tool_args
    try:
        validated_args = validate_tool_args(tool_name, tool_args)
    except ValueError as e:
        return ToolMessage(
            content=json.dumps({"error": str(e)}, ensure_ascii=False),
            tool_call_id=tool_call_id,
        )

    # 执行工具（在线程池中运行同步函数）
    start_time = time.time()
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, tool.invoke, validated_args),
            timeout=timeout,
        )

        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Tool {tool_name} executed in {elapsed:.0f}ms")

        return ToolMessage(content=str(result), tool_call_id=tool_call_id)

    except asyncio.TimeoutError:
        logger.warning(f"Tool {tool_name} timed out after {timeout}s")
        return ToolMessage(
            content=json.dumps({"error": f"工具 {tool_name} 执行超时（{timeout}s）"}, ensure_ascii=False),
            tool_call_id=tool_call_id,
        )
    except Exception as e:
        logger.exception(f"Tool {tool_name} execution failed")
        return ToolMessage(
            content=json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False),
            tool_call_id=tool_call_id,
        )


async def call_llm_async(
    llm,
    messages: list,
    tools: list | None = None,
    timeout: float = 60.0,
) -> AIMessage:
    """
    异步调用 LLM

    Args:
        llm: LangChain LLM 实例
        messages: 消息列表
        tools: 工具列表（可选）
        timeout: 超时秒数

    Returns:
        AIMessage
    """
    start_time = time.time()

    try:
        llm_with_tools = llm.bind_tools(tools) if tools else llm

        # 使用 async invoke
        if hasattr(llm_with_tools, 'ainvoke'):
            result = await asyncio.wait_for(
                llm_with_tools.ainvoke(messages),
                timeout=timeout,
            )
        else:
            # 降级：在线程池中运行
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, llm_with_tools.invoke, messages),
                timeout=timeout,
            )

        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"LLM call completed in {elapsed:.0f}ms")

        return result

    except asyncio.TimeoutError:
        logger.error(f"LLM call timed out after {timeout}s")
        return AIMessage(content=f"抱歉，AI 响应超时（{timeout}s），请稍后再试。")
    except Exception as e:
        logger.exception("LLM call failed")
        return AIMessage(content=f"抱歉，AI 服务暂时不可用（{str(e)}）。请稍后再试。")
