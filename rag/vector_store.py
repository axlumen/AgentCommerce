"""
向量语义检索

使用 FAISS IndexFlatIP 实现向量检索。
嵌入模型：优先 OpenAI text-embedding-3-small，降级 sentence-transformers。
支持结构化分块和元数据过滤。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from rag.exceptions import EmbeddingError, VectorStoreError

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """向量文档"""
    product_id: int
    chunk_type: str       # name, description, specs, full
    text: str             # 原始文本
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """FAISS 向量存储"""

    def __init__(self):
        self.index = None                  # FAISS 索引
        self.documents: list[VectorDocument] = []  # 文档列表（与索引对齐）
        self.dimension: int = 0            # 向量维度
        self._embedding_fn = None          # 嵌入函数
        self._embedding_model_type = None  # "openai" 或 "local"

    def _get_embedding_fn(self):
        """获取嵌入函数（延迟初始化）"""
        if self._embedding_fn is not None:
            return self._embedding_fn

        from config import (
            RAG_EMBEDDING_MODEL,
            RAG_EMBEDDING_DIMENSION,
            RAG_EMBEDDING_PROVIDER,
            DASHSCOPE_API_KEY,
            DASHSCOPE_BASE_URL,
        )

        # 1. 通义千问 DashScope（支持 qwen3-vl-embedding）
        if RAG_EMBEDDING_PROVIDER == "dashscope" and DASHSCOPE_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=DASHSCOPE_API_KEY,
                    base_url=DASHSCOPE_BASE_URL,
                )

                def dashscope_embed(texts: list[str]) -> np.ndarray:
                    response = client.embeddings.create(
                        model=RAG_EMBEDDING_MODEL,
                        input=texts,
                    )
                    return np.array([item.embedding for item in response.data], dtype=np.float32)

                self._embedding_fn = dashscope_embed
                self._embedding_model_type = "dashscope"
                self.dimension = RAG_EMBEDDING_DIMENSION
                logger.info(f"Using DashScope embeddings: {RAG_EMBEDDING_MODEL} (dim={self.dimension})")
                return self._embedding_fn
            except Exception as e:
                logger.warning(f"DashScope embedding not available: {e}")

        # 2. OpenAI
        if RAG_EMBEDDING_PROVIDER == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    client_kwargs = {"api_key": api_key}
                    base_url = os.getenv("OPENAI_BASE_URL")
                    if base_url:
                        client_kwargs["base_url"] = base_url
                    client = OpenAI(**client_kwargs)

                    def openai_embed(texts: list[str]) -> np.ndarray:
                        response = client.embeddings.create(
                            model=RAG_EMBEDDING_MODEL,
                            input=texts,
                        )
                        return np.array([item.embedding for item in response.data], dtype=np.float32)

                    self._embedding_fn = openai_embed
                    self._embedding_model_type = "openai"
                    self.dimension = RAG_EMBEDDING_DIMENSION
                    logger.info(f"Using OpenAI embeddings: {RAG_EMBEDDING_MODEL}")
                    return self._embedding_fn
            except Exception as e:
                logger.warning(f"OpenAI embedding not available: {e}")

        # 3. 本地 sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")

            def local_embed(texts: list[str]) -> np.ndarray:
                return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

            self._embedding_fn = local_embed
            self._embedding_model_type = "local"
            self.dimension = 384  # all-MiniLM-L6-v2 dimension
            logger.info("Using local sentence-transformers embeddings")
            return self._embedding_fn
        except Exception as e:
            logger.warning(f"Local embedding not available: {e}")

        raise EmbeddingError("No embedding model available. Configure DASHSCOPE_API_KEY or install sentence-transformers.")

    def build_index(self, products: list[dict]) -> None:
        """
        从商品列表构建向量索引

        Args:
            products: 商品字典列表
        """
        import faiss

        embed_fn = self._get_embedding_fn()

        # 生成文档和嵌入
        self.documents = []
        texts = []

        for product in products:
            product_id = product["id"]
            name = product.get("name", "")
            description = product.get("description", "")
            brand = product.get("brand", "")
            specs = product.get("specs") or {}
            price = product.get("price", 0)
            category_id = product.get("category_id")

            metadata = {
                "product_id": product_id,
                "category_id": category_id,
                "price": float(price),
                "brand": brand,
            }

            # 名称块
            self.documents.append(VectorDocument(
                product_id=product_id,
                chunk_type="name",
                text=name,
                metadata={**metadata, "chunk_type": "name"},
            ))
            texts.append(name)

            # 完整文本块（用于嵌入）
            full_text_parts = [f"商品名称：{name}"]
            if description:
                full_text_parts.append(f"描述：{description[:200]}")
            if brand:
                full_text_parts.append(f"品牌：{brand}")
            if specs:
                specs_str = "，".join(f"{k}：{v}" for k, v in specs.items())
                full_text_parts.append(f"规格：{specs_str}")
            full_text = " ".join(full_text_parts)

            self.documents.append(VectorDocument(
                product_id=product_id,
                chunk_type="full",
                text=full_text,
                metadata={**metadata, "chunk_type": "full"},
            ))
            texts.append(full_text)

        if not texts:
            logger.warning("No documents to index")
            return

        # 分批生成嵌入（DashScope 等 API 有 batch size 限制）
        try:
            batch_size = int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "10"))
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                all_embeddings.append(embed_fn(batch))
                logger.debug(f"Embedded batch {i // batch_size + 1}: {len(batch)} texts")
            embeddings = np.concatenate(all_embeddings, axis=0)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

        # 构建 FAISS 索引
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)

        # L2 归一化（使内积等于余弦相似度）
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        logger.info(f"Vector index built: {self.index.ntotal} vectors, dim={self.dimension}")

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[tuple[int, float, str]]:
        """
        向量搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 元数据过滤 {"category_id": 1, "price_max": 5000, "brand": "华为"}

        Returns:
            [(product_id, score, text), ...]
        """
        if not self.index or self.index.ntotal == 0:
            return []

        embed_fn = self._get_embedding_fn()

        try:
            query_embedding = embed_fn([query])
        except Exception as e:
            raise EmbeddingError(f"Failed to embed query: {e}")

        import faiss
        faiss.normalize_L2(query_embedding)

        # 搜索（多取一些，用于过滤后仍能返回足够结果）
        search_k = min(top_k * 3, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, search_k)

        results = []
        seen_product_ids = set()

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue

            doc = self.documents[idx]
            product_id = doc.product_id

            # 去重（同一商品只保留最高分的块）
            if product_id in seen_product_ids:
                continue

            # 元数据过滤
            if filters and not self._apply_filters(doc.metadata, filters):
                continue

            seen_product_ids.add(product_id)
            results.append((product_id, float(dist), doc.text))

            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _apply_filters(metadata: dict, filters: dict) -> bool:
        """应用元数据过滤"""
        if "category_id" in filters and metadata.get("category_id") != filters["category_id"]:
            return False
        if "price_min" in filters and metadata.get("price", 0) < filters["price_min"]:
            return False
        if "price_max" in filters and metadata.get("price", float("inf")) > filters["price_max"]:
            return False
        if "brand" in filters and metadata.get("brand", "").lower() != filters["brand"].lower():
            return False
        return True

    def save(self, path: str) -> None:
        """保存索引到文件"""
        import faiss

        if not self.index:
            return

        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        # 保存 FAISS 索引
        faiss.write_index(self.index, path)

        # 保存文档映射
        meta_path = path + ".meta.json"
        meta = [
            {
                "product_id": doc.product_id,
                "chunk_type": doc.chunk_type,
                "text": doc.text,
                "metadata": doc.metadata,
            }
            for doc in self.documents
        ]
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)

        logger.info(f"Vector index saved to {path} ({self.index.ntotal} vectors)")

    def load(self, path: str) -> bool:
        """从文件加载索引"""
        import faiss

        if not os.path.exists(path):
            return False

        try:
            self.index = faiss.read_index(path)

            meta_path = path + ".meta.json"
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self.documents = [
                    VectorDocument(
                        product_id=m["product_id"],
                        chunk_type=m["chunk_type"],
                        text=m["text"],
                        metadata=m.get("metadata", {}),
                    )
                    for m in meta
                ]

            self.dimension = self.index.d
            logger.info(f"Vector index loaded from {path} ({self.index.ntotal} vectors)")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}")
            return False


# 全局单例
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
