"""
共享 Redis 客户端

所有模块统一从此处获取 Redis 连接，避免重复初始化。
Redis 不可用时返回 None，调用方需做容错处理。
"""

import logging

from config import REDIS_HOST, REDIS_PORT, REDIS_DB

logger = logging.getLogger(__name__)

_redis = None
_initialized = False


def get_redis():
    """
    获取 Redis 客户端实例

    Returns:
        Redis 实例，或 None（Redis 不可用时）
    """
    if _initialized:
        return _redis

    try:
        import redis
        _redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
        _redis.ping()
        logger.info("Redis connected: %s:%s/%s", REDIS_HOST, REDIS_PORT, REDIS_DB)
    except Exception as e:
        _redis = None
        logger.warning("Redis unavailable, features degraded: %s", e)

    _initialized = True
    return _redis
