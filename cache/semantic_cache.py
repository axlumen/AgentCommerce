"""
语义缓存

使用 Redis 存储 query_embedding → 缓存答案。
相似度阈值（0.9）以上直接返回缓存。
支持缓存失效（商品更新时清除）和命中率统计。

Redis 存储结构：
- ai_cache:{cache_id}       → Hash: query, embedding, answer, product_ids, created_at, hit_count
- ai_cache:entries           → Set: 所有 cache_id（用于遍历匹配）
- ai_cache:product:{pid}     → Set: 关联此商品的 cache_id（用于失效）
- ai_cache:stats:hits        → String: 命中次数
- ai_cache:stats:misses      → String: 未命中次数
"""

import json
import logging
import time
import uuid

import numpy as np

from redis_client import get_redis

logger = logging.getLogger(__name__)


class SemanticCache:
    """语义缓存"""

    PREFIX = "ai_cache:"
    STATS_PREFIX = "ai_cache:stats:"

    def __init__(
        self,
        similarity_threshold: float = 0.9,
        ttl: int = 3600,
        max_entries: int = 10000,
    ):
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl
        self.max_entries = max_entries
        self._embedding_fn = None

    def _get_embedding_fn(self):
        """获取嵌入函数（复用 vector_store 的）"""
        if self._embedding_fn is not None:
            return self._embedding_fn

        try:
            from rag.vector_store import get_vector_store
            vs = get_vector_store()
            self._embedding_fn = vs._get_embedding_fn()
            return self._embedding_fn
        except Exception as e:
            logger.warning(f"Cannot get embedding function for cache: {e}")
            return None

    def get(self, query: str) -> dict | None:
        """
        查询语义缓存

        Args:
            query: 用户查询

        Returns:
            缓存的响应字典，未命中返回 None
        """
        r = get_redis()
        if not r:
            return None

        embed_fn = self._get_embedding_fn()
        if not embed_fn:
            return None

        try:
            # 生成查询嵌入
            query_embedding = embed_fn([query])[0].tolist()

            # 遍历所有缓存条目，找最相似的
            entry_ids = r.smembers(f"{self.PREFIX}entries")
            if not entry_ids:
                self._incr_stat("misses")
                return None

            best_similarity = 0.0
            best_entry = None

            for entry_id in entry_ids:
                entry_data = r.hgetall(f"{self.PREFIX}{entry_id}")
                if not entry_data:
                    continue

                cached_embedding_str = entry_data.get("embedding")
                if not cached_embedding_str:
                    continue

                try:
                    cached_embedding = np.array(json.loads(cached_embedding_str), dtype=np.float32)
                    query_vec = np.array(query_embedding, dtype=np.float32)

                    # 余弦相似度
                    similarity = np.dot(query_vec, cached_embedding) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(cached_embedding) + 1e-8
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_entry = entry_data
                        best_entry["_id"] = entry_id
                except Exception:
                    continue

            if best_entry and best_similarity >= self.similarity_threshold:
                # 命中
                self._incr_stat("hits")
                r.hincrby(f"{self.PREFIX}{best_entry['_id']}", "hit_count", 1)

                logger.info(f"Semantic cache HIT (similarity={best_similarity:.4f})")
                return {
                    "answer": best_entry.get("answer", ""),
                    "product_ids": json.loads(best_entry.get("product_ids", "[]")),
                    "similarity": round(best_similarity, 4),
                    "cache_id": best_entry["_id"],
                    "hit_count": int(best_entry.get("hit_count", 0)) + 1,
                }

            # 未命中
            self._incr_stat("misses")
            return None

        except Exception as e:
            logger.error(f"Semantic cache get failed: {e}")
            return None

    def set(
        self,
        query: str,
        answer: str,
        product_ids: list[int] | None = None,
    ) -> str | None:
        """
        写入语义缓存

        Args:
            query: 用户查询
            answer: AI 回答
            product_ids: 相关商品 ID 列表

        Returns:
            cache_id，失败返回 None
        """
        r = get_redis()
        if not r:
            return None

        embed_fn = self._get_embedding_fn()
        if not embed_fn:
            return None

        try:
            # 生成嵌入
            embedding = embed_fn([query])[0].tolist()

            # 生成 cache_id
            cache_id = uuid.uuid4().hex[:16]

            # 存储缓存条目
            pipe = r.pipeline()
            pipe.hset(f"{self.PREFIX}{cache_id}", mapping={
                "query": query,
                "embedding": json.dumps(embedding),
                "answer": answer,
                "product_ids": json.dumps(product_ids or []),
                "created_at": str(time.time()),
                "hit_count": "0",
            })
            pipe.expire(f"{self.PREFIX}{cache_id}", self.ttl)

            # 添加到条目集合
            pipe.sadd(f"{self.PREFIX}entries", cache_id)

            # 建立商品→缓存映射
            if product_ids:
                for pid in product_ids:
                    pipe.sadd(f"{self.PREFIX}product:{pid}", cache_id)

            # 限制条目数量
            pipe.execute()

            self._enforce_max_entries(r)

            logger.info(f"Semantic cache SET: {cache_id} (query='{query[:50]}')")
            return cache_id

        except Exception as e:
            logger.error(f"Semantic cache set failed: {e}")
            return None

    def invalidate_by_product(self, product_ids: list[int]) -> int:
        """
        商品更新时清除相关缓存

        Args:
            product_ids: 更新的商品 ID 列表

        Returns:
            清除的缓存条目数
        """
        r = get_redis()
        if not r:
            return 0

        removed = 0
        try:
            for pid in product_ids:
                mapping_key = f"{self.PREFIX}product:{pid}"
                cache_ids = r.smembers(mapping_key)

                if cache_ids:
                    pipe = r.pipeline()
                    for cid in cache_ids:
                        pipe.delete(f"{self.PREFIX}{cid}")
                        pipe.srem(f"{self.PREFIX}entries", cid)
                    pipe.delete(mapping_key)
                    pipe.execute()
                    removed += len(cache_ids)

            if removed:
                logger.info(f"Invalidated {removed} cache entries for products {product_ids}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")

        return removed

    def invalidate_all(self) -> None:
        """清除所有缓存"""
        r = get_redis()
        if not r:
            return

        try:
            entry_ids = r.smembers(f"{self.PREFIX}entries")
            if entry_ids:
                pipe = r.pipeline()
                for eid in entry_ids:
                    pipe.delete(f"{self.PREFIX}{eid}")
                pipe.delete(f"{self.PREFIX}entries")

                # 清除商品映射
                product_keys = r.keys(f"{self.PREFIX}product:*")
                if product_keys:
                    for key in product_keys:
                        pipe.delete(key)

                pipe.execute()
            logger.info("All semantic cache invalidated")
        except Exception as e:
            logger.error(f"Cache invalidation all failed: {e}")

    def stats(self) -> dict:
        """获取缓存统计"""
        r = get_redis()
        if not r:
            return {"available": False}

        try:
            hits = int(r.get(f"{self.STATS_PREFIX}hits") or 0)
            misses = int(r.get(f"{self.STATS_PREFIX}misses") or 0)
            total = hits + misses
            entry_count = r.scard(f"{self.PREFIX}entries") or 0

            return {
                "available": True,
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate": round(hits / total, 4) if total > 0 else 0.0,
                "entry_count": entry_count,
                "similarity_threshold": self.similarity_threshold,
                "ttl": self.ttl,
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

    def _incr_stat(self, field: str) -> None:
        """递增统计计数器"""
        r = get_redis()
        if r:
            try:
                r.incr(f"{self.STATS_PREFIX}{field}")
            except Exception as e:
                logger.debug(f"Failed to incr stat {field}: {e}")

    def _enforce_max_entries(self, r) -> None:
        """限制缓存条目数量"""
        try:
            count = r.scard(f"{self.PREFIX}entries")
            if count and count > self.max_entries:
                # 删除最旧的条目
                excess = count - self.max_entries
                entry_ids = r.smembers(f"{self.PREFIX}entries")

                # 按创建时间排序，删除最旧的
                entries_with_time = []
                for eid in entry_ids:
                    created = r.hget(f"{self.PREFIX}{eid}", "created_at")
                    if created:
                        entries_with_time.append((eid, float(created)))

                entries_with_time.sort(key=lambda x: x[1])

                pipe = r.pipeline()
                for eid, _ in entries_with_time[:excess]:
                    pipe.delete(f"{self.PREFIX}{eid}")
                    pipe.srem(f"{self.PREFIX}entries", eid)
                pipe.execute()

        except Exception as e:
            logger.debug(f"Failed to enforce max entries: {e}")


# 全局单例
semantic_cache = SemanticCache()
