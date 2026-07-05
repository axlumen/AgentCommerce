"""
混合检索器

三级检索融合：
  query → BM25(top_k=20) ─┐
          → Vector(top_k=20)─┤→ Reranker(top_k=5) → 最终结果
          → 元数据过滤(可选) ─┘

分数归一化：BM25 和向量分数分别 min-max 归一化到 [0,1]
融合策略：final_score = α * bm25_norm + β * vector_norm + γ * reranker_score
降级策略：各级独立降级，确保系统可用性
"""

import logging
import time
from dataclasses import dataclass, field

from rag.bm25 import get_bm25_index
from rag.exceptions import RAGError
from rag.reranker import get_reranker
from rag.tokenizer import get_tokenizer
from rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """混合检索结果"""
    product_id: int
    score: float               # 最终融合分数
    bm25_score: float = 0.0    # BM25 归一化分数
    vector_score: float = 0.0  # 向量归一化分数
    reranker_score: float = 0.0  # Reranker 分数
    text: str = ""             # 匹配的文本片段


class HybridRetriever:
    """三级混合检索器"""

    def __init__(
        self,
        alpha: float = 0.3,     # BM25 权重
        beta: float = 0.3,      # 向量权重
        gamma: float = 0.4,     # Reranker 权重
        top_k_bm25: int = 20,
        top_k_vector: int = 20,
        top_k_final: int = 5,
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.top_k_bm25 = top_k_bm25
        self.top_k_vector = top_k_vector
        self.top_k_final = top_k_final

        # 各层可用性
        self._bm25_available = False
        self._vector_available = False
        self._reranker_available = False

    def build_index(self, products: list[dict]) -> None:
        """
        构建所有索引

        Args:
            products: 商品字典列表
        """
        # 构建 BM25 索引
        try:
            bm25 = get_bm25_index()
            bm25.build_index(products)
            self._bm25_available = True
            logger.info("BM25 index built successfully")
        except Exception as e:
            logger.error(f"BM25 index build failed: {e}")

        # 构建向量索引
        try:
            vs = get_vector_store()
            vs.build_index(products)
            self._vector_available = True
            logger.info("Vector index built successfully")

            # 尝试保存索引
            try:
                from config import RAG_FAISS_INDEX_PATH
                vs.save(RAG_FAISS_INDEX_PATH)
            except Exception as e:
                logger.warning(f"Failed to save vector index: {e}")
        except Exception as e:
            logger.error(f"Vector index build failed: {e}")

        # 检查 Reranker
        try:
            reranker = get_reranker()
            self._reranker_available = reranker.is_available()
        except Exception as e:
            logger.error(f"Reranker check failed: {e}")

        logger.info(
            f"Hybrid retriever status: BM25={self._bm25_available}, "
            f"Vector={self._vector_available}, Reranker={self._reranker_available}"
        )

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[HybridSearchResult]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回数量（默认使用 self.top_k_final）
            filters: 元数据过滤 {"category_id": 1, "price_max": 5000, "brand": "华为"}

        Returns:
            [HybridSearchResult, ...] 按融合分数降序
        """
        if top_k is None:
            top_k = self.top_k_final

        start_time = time.time()

        # 输入校验
        if not query or not query.strip():
            return []

        # 同义词扩展（用于 BM25）
        tokenizer = get_tokenizer()
        expanded_query = " ".join(tokenizer.tokenize_for_search(query))

        # 三层检索
        bm25_results = self._bm25_search(expanded_query, filters)
        vector_results = self._vector_search(query, filters)

        # 融合 BM25 + 向量
        merged = self._merge_results(bm25_results, vector_results)

        # Reranker 重排
        if self._reranker_available and merged:
            merged = self._apply_reranker(query, merged, top_k)

        # 取 top_k
        results = merged[:top_k]

        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"Hybrid search: query='{query[:30]}', results={len(results)}, "
            f"bm25={len(bm25_results)}, vector={len(vector_results)}, "
            f"time={elapsed:.0f}ms"
        )

        return results

    def _bm25_search(self, query: str, filters: dict | None) -> dict[int, float]:
        """BM25 检索"""
        if not self._bm25_available:
            return {}

        try:
            bm25 = get_bm25_index()
            results = bm25.search(query, top_k=self.top_k_bm25)

            # 元数据过滤
            if filters and results:
                results = self._apply_product_filters(results, filters)

            return dict(results)
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return {}

    def _vector_search(self, query: str, filters: dict | None) -> dict[int, float]:
        """向量检索"""
        if not self._vector_available:
            return {}

        try:
            vs = get_vector_store()
            results = vs.search(query, top_k=self.top_k_vector, filters=filters)
            return {pid: score for pid, score, _ in results}
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            self._vector_available = False
            return {}

    def _merge_results(
        self,
        bm25_results: dict[int, float],
        vector_results: dict[int, float],
    ) -> list[HybridSearchResult]:
        """
        融合 BM25 和向量检索结果

        分数归一化：min-max 归一化到 [0,1]
        融合公式：score = α * bm25_norm + β * vector_norm
        """
        all_product_ids = set(bm25_results.keys()) | set(vector_results.keys())
        if not all_product_ids:
            return []

        # 归一化 BM25 分数
        bm25_norm = self._normalize_scores(bm25_results)
        vector_norm = self._normalize_scores(vector_results)

        # 融合
        results = []
        for pid in all_product_ids:
            b_score = bm25_norm.get(pid, 0.0)
            v_score = vector_norm.get(pid, 0.0)

            # 加权融合（无 reranker 时，重新分配权重）
            if self._reranker_available:
                final_score = self.alpha * b_score + self.beta * v_score
            else:
                # 无 reranker，BM25 和向量各占 50%
                total_weight = self.alpha + self.beta
                if total_weight > 0:
                    final_score = (self.alpha * b_score + self.beta * v_score) / total_weight
                else:
                    final_score = 0.0

            results.append(HybridSearchResult(
                product_id=pid,
                score=final_score,
                bm25_score=b_score,
                vector_score=v_score,
            ))

        # 按融合分数降序
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _apply_reranker(
        self,
        query: str,
        merged: list[HybridSearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """应用 Reranker 重排"""
        try:
            reranker = get_reranker()

            # 构建 reranker 输入
            documents = [
                (r.product_id, r.score, f"商品ID:{r.product_id}")
                for r in merged
            ]

            reranked = reranker.rerank(query, documents, top_k=len(merged))

            # 归一化 reranker 分数
            reranker_scores = {pid: score for pid, score in reranked}
            reranker_norm = self._normalize_scores(reranker_scores)

            # 更新融合分数
            for result in merged:
                r_score = reranker_norm.get(result.product_id, 0.0)
                result.reranker_score = r_score
                result.score = (
                    self.alpha * result.bm25_score +
                    self.beta * result.vector_score +
                    self.gamma * r_score
                )

            # 重新排序
            merged.sort(key=lambda x: x.score, reverse=True)
            return merged

        except Exception as e:
            logger.error(f"Reranker failed: {e}")
            self._reranker_available = False
            return merged

    @staticmethod
    def _normalize_scores(scores: dict[int, float]) -> dict[int, float]:
        """Min-Max 归一化到 [0, 1]"""
        if not scores:
            return {}

        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val

        if range_val == 0:
            return {k: 1.0 for k in scores}

        return {k: (v - min_val) / range_val for k, v in scores.items()}

    @staticmethod
    def _apply_product_filters(
        results: list[tuple[int, float]],
        filters: dict,
    ) -> list[tuple[int, float]]:
        """对 BM25 结果应用商品级过滤"""
        from database import SessionLocal
        from models.product import Product

        db = SessionLocal()
        try:
            product_ids = [pid for pid, _ in results]
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            product_map = {p.id: p for p in products}

            filtered = []
            for pid, score in results:
                product = product_map.get(pid)
                if not product:
                    continue

                if "category_id" in filters and product.category_id != filters["category_id"]:
                    continue
                if "price_min" in filters and float(product.price) < filters["price_min"]:
                    continue
                if "price_max" in filters and float(product.price) > filters["price_max"]:
                    continue
                if "brand" in filters:
                    if not product.brand or product.brand.lower() != filters["brand"].lower():
                        continue

                filtered.append((pid, score))
            return filtered
        finally:
            db.close()

    def get_status(self) -> dict:
        """获取检索器状态"""
        return {
            "bm25_available": self._bm25_available,
            "vector_available": self._vector_available,
            "reranker_available": self._reranker_available,
            "mode": self._get_mode(),
        }

    def _get_mode(self) -> str:
        """获取当前检索模式"""
        if self._bm25_available and self._vector_available and self._reranker_available:
            return "full_hybrid"
        elif self._bm25_available and self._vector_available:
            return "bm25_vector"
        elif self._bm25_available:
            return "bm25_only"
        elif self._vector_available:
            return "vector_only"
        else:
            return "fallback"


# 全局单例
_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    """获取混合检索器单例"""
    global _retriever
    if _retriever is None:
        from config import RAG_ALPHA, RAG_BETA, RAG_GAMMA, RAG_TOP_K_BM25, RAG_TOP_K_VECTOR, RAG_TOP_K_FINAL
        _retriever = HybridRetriever(
            alpha=RAG_ALPHA,
            beta=RAG_BETA,
            gamma=RAG_GAMMA,
            top_k_bm25=RAG_TOP_K_BM25,
            top_k_vector=RAG_TOP_K_VECTOR,
            top_k_final=RAG_TOP_K_FINAL,
        )
    return _retriever


def fallback_search(query: str, db_session=None, top_k: int = 5) -> list[dict]:
    """
    降级搜索：当混合检索不可用时，回退到 MySQL LIKE 查询

    Args:
        query: 查询文本
        db_session: 数据库会话
        top_k: 返回数量

    Returns:
        商品字典列表
    """
    from database import SessionLocal
    from models.product import Product
    from sqlalchemy import or_

    db = db_session or SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.is_on_sale == True,
            or_(
                Product.name.contains(query),
                Product.description.contains(query),
            )
        ).limit(top_k).all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description or "",
                "price": float(p.price),
                "stock": p.stock,
                "category_id": p.category_id,
                "brand": p.brand,
                "specs": p.specs,
            }
            for p in products
        ]
    finally:
        if not db_session:
            db.close()
