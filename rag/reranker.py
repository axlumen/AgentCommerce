"""
Cross-Encoder Reranker

使用 sentence-transformers CrossEncoder 对检索结果重排序。
模型：cross-encoder/ms-marco-MiniLM-L6-v2（轻量级，CPU 推理 <100ms）
模型预加载（单例模式），异常时降级为原始排序。
"""

import logging
import time

from rag.exceptions import RerankerError

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-Encoder 重排序器"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._loaded = False
        self._load_failed = False

    def _ensure_loaded(self) -> bool:
        """确保模型已加载"""
        if self._loaded:
            return self._model is not None

        if self._load_failed:
            return False

        try:
            from sentence_transformers import CrossEncoder
            start = time.time()
            self._model = CrossEncoder(self.model_name)
            elapsed = (time.time() - start) * 1000
            logger.info(f"Reranker model loaded in {elapsed:.0f}ms: {self.model_name}")
            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self._load_failed = True
            self._loaded = True
            return False

    def rerank(
        self,
        query: str,
        documents: list[tuple[int, float, str]],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """
        重排序检索结果

        Args:
            query: 查询文本
            documents: [(product_id, original_score, text), ...]
            top_k: 返回前 K 个结果

        Returns:
            [(product_id, reranker_score), ...] 按重排序分数降序
        """
        if not documents:
            return []

        if not self._ensure_loaded():
            # 模型不可用，降级为原始排序
            logger.warning("Reranker unavailable, falling back to original ranking")
            return [(pid, score) for pid, score, _ in documents[:top_k]]

        try:
            start = time.time()

            # 构建 query-document 对
            pairs = [[query, doc_text] for _, _, doc_text in documents]

            # 重排序
            scores = self._model.predict(pairs)

            # 组合结果
            results = []
            for i, (product_id, _, _) in enumerate(documents):
                results.append((product_id, float(scores[i])))

            # 按分数降序排列
            results.sort(key=lambda x: x[1], reverse=True)

            elapsed = (time.time() - start) * 1000
            logger.debug(f"Reranked {len(documents)} docs in {elapsed:.0f}ms")

            return results[:top_k]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # 降级为原始排序
            return [(pid, score) for pid, score, _ in documents[:top_k]]

    def is_available(self) -> bool:
        """检查 reranker 是否可用"""
        return self._ensure_loaded()


# 全局单例
_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """获取 Reranker 单例"""
    global _reranker
    if _reranker is None:
        from config import RAG_RERANKER_MODEL
        _reranker = Reranker(model_name=RAG_RERANKER_MODEL)
    return _reranker
