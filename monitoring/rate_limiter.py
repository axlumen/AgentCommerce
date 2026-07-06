"""
滑动窗口限流器（Redis）

使用 Redis ZSET 实现滑动窗口限流。
每用户每分钟限制 N 次 AI 调用。
"""

import logging
import time
import uuid

from redis_client import get_redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    滑动窗口限流器

    使用 Redis ZSET 实现：
    - Key: ratelimit:{identifier}
    - Score: timestamp (float)
    - Member: unique_id (避免重复)

    当窗口内的请求数超过 limit 时，拒绝请求。
    """

    def __init__(self, prefix: str = "ratelimit:"):
        self.prefix = prefix

    def check(
        self,
        identifier: str,
        limit: int = 30,
        window_seconds: int = 60,
    ) -> tuple[bool, dict]:
        """
        检查是否超过限流

        Args:
            identifier: 限流标识（通常是 user_id 或 IP）
            limit: 窗口内最大请求数
            window_seconds: 窗口大小（秒）

        Returns:
            (allowed, info):
            - allowed: True=允许, False=拒绝
            - info: {"current": int, "limit": int, "reset_at": float}
        """
        r = get_redis()
        if not r:
            # Redis 不可用时放行
            return True, {"current": 0, "limit": limit, "reset_at": 0, "fallback": True}

        key = f"{self.prefix}{identifier}"
        now = time.time()
        window_start = now - window_seconds

        try:
            pipe = r.pipeline()

            # 清除窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 统计窗口内的请求数
            pipe.zcard(key)

            # 添加当前请求
            member = f"{now}:{uuid.uuid4().hex[:8]}"
            pipe.zadd(key, {member: now})

            # 设置 key 过期（自动清理）
            pipe.expire(key, window_seconds + 1)

            results = pipe.execute()
            current_count = results[1]  # zcard 结果

            allowed = current_count < limit
            reset_at = now + window_seconds

            return allowed, {
                "current": current_count + 1,  # +1 包含当前请求
                "limit": limit,
                "reset_at": reset_at,
                "remaining": max(0, limit - current_count - 1),
            }

        except Exception as e:
            logger.warning(f"Rate limiter check failed: {e}")
            return True, {"current": 0, "limit": limit, "reset_at": 0, "error": str(e)}

    def get_usage(self, identifier: str, window_seconds: int = 60) -> int:
        """获取当前窗口内的请求数"""
        r = get_redis()
        if not r:
            return 0

        key = f"{self.prefix}{identifier}"
        now = time.time()
        window_start = now - window_seconds

        try:
            r.zremrangebyscore(key, 0, window_start)
            return r.zcard(key)
        except Exception:
            return 0

    def reset(self, identifier: str) -> None:
        """重置指定标识的限流计数"""
        r = get_redis()
        if not r:
            return

        key = f"{self.prefix}{identifier}"
        try:
            r.delete(key)
        except Exception as e:
            logger.debug(f"Rate limiter reset failed: {e}")


# 全局单例
rate_limiter = RateLimiter()
