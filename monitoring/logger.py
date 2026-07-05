"""
结构化日志 + 统计指标

职责：
- AI 调用日志：输入、输出、token 数、耗时、模型版本
- Agent 决策追踪：每一步思考、工具调用、结果
- 错误日志：失败原因、重试次数
- 统计指标：调用量、成功率、平均耗时、平均 token 消耗
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis 客户端（延迟初始化）
_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        try:
            import redis
            from config import REDIS_HOST, REDIS_PORT, REDIS_DB
            _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
            _redis.ping()
        except Exception:
            _redis = False
    return _redis if _redis is not False else None


# ============================================================
# 数据结构
# ============================================================


@dataclass
class AICallLog:
    """AI 调用日志"""
    timestamp: float = field(default_factory=time.time)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: str = ""
    input_preview: str = ""     # 输入摘要（前 200 字符）
    output_preview: str = ""    # 输出摘要（前 200 字符）
    call_type: str = "llm"     # llm / embedding / reranker
    user_id: int | None = None
    session_id: str | None = None


@dataclass
class AgentTrace:
    """Agent 决策追踪"""
    session_id: str = ""
    user_id: int | None = None
    step: int = 0
    node: str = ""              # agent_node / tool_node / human_node
    thought: str = ""           # LLM 思考内容
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    tool_result: str = ""
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error: str = ""


# ============================================================
# 日志记录
# ============================================================


def log_ai_call(call_log: AICallLog) -> None:
    """
    记录 AI 调用日志

    写入 Python logger + 更新 Redis 统计计数器
    """
    # 写入 logger
    log_data = {
        "type": "ai_call",
        "model": call_log.model,
        "latency_ms": round(call_log.latency_ms, 1),
        "input_tokens": call_log.input_tokens,
        "output_tokens": call_log.output_tokens,
        "success": call_log.success,
        "call_type": call_log.call_type,
    }
    if call_log.error:
        log_data["error"] = call_log.error

    if call_log.success:
        logger.info("AI call completed", extra={"ai_log": log_data})
    else:
        logger.warning("AI call failed", extra={"ai_log": log_data})

    # 更新 Redis 统计
    _update_stats(call_log)


def log_agent_trace(trace: AgentTrace) -> None:
    """
    记录 Agent 决策追踪

    写入 Python logger
    """
    log_data = {
        "type": "agent_trace",
        "session_id": trace.session_id,
        "step": trace.step,
        "node": trace.node,
        "tool_name": trace.tool_name,
        "latency_ms": round(trace.latency_ms, 1),
        "success": trace.success,
    }
    if trace.thought:
        log_data["thought"] = trace.thought[:200]
    if trace.error:
        log_data["error"] = trace.error

    logger.info("Agent trace", extra={"agent_trace": log_data})


def log_error(error_type: str, message: str, context: dict | None = None) -> None:
    """记录错误日志"""
    log_data = {
        "type": "error",
        "error_type": error_type,
        "message": message,
    }
    if context:
        log_data["context"] = context
    logger.error(f"[{error_type}] {message}", extra={"error_log": log_data})


# ============================================================
# 统计指标（Redis 计数器）
# ============================================================

STATS_PREFIX = "ai:stats:"


def _update_stats(call_log: AICallLog) -> None:
    """更新 Redis 统计计数器"""
    r = _get_redis()
    if not r:
        return

    try:
        pipe = r.pipeline()
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 总调用次数
        pipe.incr(f"{STATS_PREFIX}calls:total")
        pipe.incr(f"{STATS_PREFIX}calls:{date_str}")

        # 成功/失败
        if call_log.success:
            pipe.incr(f"{STATS_PREFIX}calls:success")
        else:
            pipe.incr(f"{STATS_PREFIX}calls:error")

        # 延迟（用累计值计算平均）
        latency_ms = int(call_log.latency_ms)
        pipe.incrby(f"{STATS_PREFIX}latency:sum", latency_ms)

        # Token
        if call_log.input_tokens:
            pipe.incrby(f"{STATS_PREFIX}tokens:input", call_log.input_tokens)
        if call_log.output_tokens:
            pipe.incrby(f"{STATS_PREFIX}tokens:output", call_log.output_tokens)

        # 按调用类型统计
        pipe.incr(f"{STATS_PREFIX}calls:type:{call_log.call_type}")

        pipe.execute()
    except Exception as e:
        logger.warning(f"Failed to update stats: {e}")


def get_stats() -> dict:
    """
    获取统计指标

    Returns:
        {
            "total_calls": int,
            "success_calls": int,
            "error_calls": int,
            "success_rate": float,
            "avg_latency_ms": float,
            "total_input_tokens": int,
            "total_output_tokens": int,
            "avg_input_tokens": float,
            "avg_output_tokens": float,
        }
    """
    r = _get_redis()
    if not r:
        return {"error": "Redis not available"}

    try:
        pipe = r.pipeline()
        pipe.get(f"{STATS_PREFIX}calls:total")
        pipe.get(f"{STATS_PREFIX}calls:success")
        pipe.get(f"{STATS_PREFIX}calls:error")
        pipe.get(f"{STATS_PREFIX}latency:sum")
        pipe.get(f"{STATS_PREFIX}tokens:input")
        pipe.get(f"{STATS_PREFIX}tokens:output")
        results = pipe.execute()

        total = int(results[0] or 0)
        success = int(results[1] or 0)
        error = int(results[2] or 0)
        latency_sum = int(results[3] or 0)
        input_tokens = int(results[4] or 0)
        output_tokens = int(results[5] or 0)

        return {
            "total_calls": total,
            "success_calls": success,
            "error_calls": error,
            "success_rate": round(success / total, 4) if total > 0 else 0.0,
            "avg_latency_ms": round(latency_sum / total, 1) if total > 0 else 0.0,
            "total_input_tokens": input_tokens,
            "total_output_tokens": output_tokens,
            "avg_input_tokens": round(input_tokens / total, 1) if total > 0 else 0.0,
            "avg_output_tokens": round(output_tokens / total, 1) if total > 0 else 0.0,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e)}


def get_stats_by_date(date_str: str) -> dict:
    """获取指定日期的调用次数"""
    r = _get_redis()
    if not r:
        return {"error": "Redis not available"}

    try:
        count = r.get(f"{STATS_PREFIX}calls:{date_str}")
        return {"date": date_str, "calls": int(count or 0)}
    except Exception as e:
        return {"error": str(e)}


def reset_stats() -> None:
    """重置所有统计（测试用）"""
    r = _get_redis()
    if not r:
        return

    try:
        keys = r.keys(f"{STATS_PREFIX}*")
        if keys:
            r.delete(*keys)
    except Exception as e:
        logger.debug(f"Failed to reset stats: {e}")
