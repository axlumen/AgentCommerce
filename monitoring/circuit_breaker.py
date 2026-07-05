"""
熔断器（三状态机）

状态流转：
  CLOSED ──连续失败≥阈值──→ OPEN ──超时──→ HALF_OPEN ──成功──→ CLOSED
    ↑                        │                 │
    └──────成功──────────────┘                 └──失败──→ OPEN
"""

import logging
import time

logger = logging.getLogger(__name__)

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


# 状态常量
CLOSED = "CLOSED"
OPEN = "OPEN"
HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    熔断器

    使用 Redis 存储状态，支持分布式部署。

    Redis Key:
    - cb:{name}:state      → CLOSED/OPEN/HALF_OPEN
    - cb:{name}:failures   → 连续失败次数
    - cb:{name}:last_fail  → 上次失败时间戳
    - cb:{name}:half_open_calls → HALF_OPEN 状态下的试探调用次数
    """

    def __init__(
        self,
        name: str = "ai_service",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._prefix = f"cb:{name}:"

    def _get(self, field: str, default: str = "") -> str:
        """获取 Redis 字段"""
        r = _get_redis()
        if not r:
            return default
        try:
            val = r.get(f"{self._prefix}{field}")
            return val if val else default
        except Exception:
            return default

    def _set(self, field: str, value: str, ttl: int | None = None) -> None:
        """设置 Redis 字段"""
        r = _get_redis()
        if not r:
            return
        try:
            key = f"{self._prefix}{field}"
            if ttl:
                r.setex(key, ttl, value)
            else:
                r.set(key, value)
        except Exception as e:
            logger.debug(f"Circuit breaker set {field} failed: {e}")

    def _incr(self, field: str) -> int:
        """递增 Redis 计数器"""
        r = _get_redis()
        if not r:
            return 0
        try:
            return r.incr(f"{self._prefix}{field}")
        except Exception:
            return 0

    def state(self) -> str:
        """获取当前状态"""
        state = self._get("state", CLOSED)

        # OPEN 状态下检查是否超时 → 转为 HALF_OPEN
        if state == OPEN:
            last_fail = float(self._get("last_fail", "0"))
            if time.time() - last_fail >= self.recovery_timeout:
                self._set("state", HALF_OPEN)
                self._set("half_open_calls", "0")
                logger.info(f"Circuit breaker [{self.name}] OPEN → HALF_OPEN")
                return HALF_OPEN

        return state

    def call(self, fn, *args, **kwargs):
        """
        执行调用（自动熔断）

        Args:
            fn: 要执行的函数

        Returns:
            fn 的返回值

        Raises:
            CircuitOpenError: 熔断器打开时抛出
        """
        current_state = self.state()

        if current_state == OPEN:
            raise CircuitOpenError(
                f"Circuit breaker [{self.name}] is OPEN. "
                f"Recovery in {self._time_until_recovery():.0f}s"
            )

        if current_state == HALF_OPEN:
            # 半开状态：限制试探调用数
            calls = int(self._get("half_open_calls", "0"))
            if calls >= self.half_open_max_calls:
                raise CircuitOpenError(
                    f"Circuit breaker [{self.name}] is HALF_OPEN, max calls reached"
                )
            self._set("half_open_calls", str(calls + 1))

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def call_async(self, fn, *args, **kwargs):
        """异步版本的 call"""
        current_state = self.state()

        if current_state == OPEN:
            raise CircuitOpenError(
                f"Circuit breaker [{self.name}] is OPEN. "
                f"Recovery in {self._time_until_recovery():.0f}s"
            )

        if current_state == HALF_OPEN:
            calls = int(self._get("half_open_calls", "0"))
            if calls >= self.half_open_max_calls:
                raise CircuitOpenError(
                    f"Circuit breaker [{self.name}] is HALF_OPEN, max calls reached"
                )
            self._set("half_open_calls", str(calls + 1))

        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """成功回调"""
        current_state = self.state()
        if current_state == HALF_OPEN:
            # 半开状态成功 → 关闭熔断器
            self._set("state", CLOSED)
            self._set("failures", "0")
            logger.info(f"Circuit breaker [{self.name}] HALF_OPEN → CLOSED")
        elif current_state == CLOSED:
            # 闭合状态成功 → 重置失败计数
            self._set("failures", "0")

    def _on_failure(self) -> None:
        """失败回调"""
        r = _get_redis()
        if not r:
            return

        try:
            pipe = r.pipeline()
            pipe.incr(f"{self._prefix}failures")
            pipe.set(f"{self._prefix}last_fail", str(time.time()))
            results = pipe.execute()
            failures = int(results[0])

            current_state = self.state()

            if current_state == HALF_OPEN:
                # 半开状态失败 → 重新打开
                self._set("state", OPEN)
                logger.warning(f"Circuit breaker [{self.name}] HALF_OPEN → OPEN (failure in half-open)")

            elif current_state == CLOSED and failures >= self.failure_threshold:
                # 闭合状态连续失败 → 打开
                self._set("state", OPEN)
                logger.warning(f"Circuit breaker [{self.name}] CLOSED → OPEN (failures={failures})")

        except Exception as e:
            logger.error(f"Failed to record circuit breaker failure: {e}")

    def _time_until_recovery(self) -> float:
        """计算距离恢复的剩余秒数"""
        last_fail = float(self._get("last_fail", "0"))
        elapsed = time.time() - last_fail
        return max(0, self.recovery_timeout - elapsed)

    def reset(self) -> None:
        """手动重置熔断器"""
        r = _get_redis()
        if not r:
            return
        try:
            keys = r.keys(f"{self._prefix}*")
            if keys:
                r.delete(*keys)
        except Exception as e:
            logger.debug(f"Circuit breaker reset failed: {e}")

    def get_info(self) -> dict:
        """获取熔断器信息"""
        return {
            "name": self.name,
            "state": self.state(),
            "failures": int(self._get("failures", "0")),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "time_until_recovery": round(self._time_until_recovery(), 1),
        }


class CircuitOpenError(Exception):
    """熔断器打开异常"""
    pass


# 全局单例
ai_circuit_breaker = CircuitBreaker(
    name="ai_service",
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3,
)
