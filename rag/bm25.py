"""
BM25 关键词检索

纯 Python 实现 BM25，不依赖 Elasticsearch。
使用内存倒排索引，支持增量更新。
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field

from rag.exceptions import BM25IndexError
from rag.tokenizer import get_tokenizer

logger = logging.getLogger(__name__)


@dataclass
class BM25Document:
    """BM25 文档"""
    product_id: int
    tokens: list[str]
    token_freq: dict[str, int] = field(default_factory=dict)
    doc_len: int = 0

    def __post_init__(self):
        if self.tokens and not self.token_freq:
            freq = defaultdict(int)
            for token in self.tokens:
                freq[token] += 1
            self.token_freq = dict(freq)
            self.doc_len = len(self.tokens)


class BM25Index:
    """
    BM25 倒排索引

    BM25 公式：
    score(D, Q) = Σ IDF(qi) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |D| / avgdl))

    其中：
    - IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
    - tf = 词频
    - k1 = 1.5（词频饱和参数）
    - b = 0.75（文档长度归一化参数）
    - |D| = 文档长度
    - avgdl = 平均文档长度
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        # 倒排索引：term → [(product_id, tf), ...]
        self.inverted_index: dict[str, list[tuple[int, int]]] = defaultdict(list)

        # 文档存储
        self.documents: dict[int, BM25Document] = {}

        # 统计信息
        self.doc_count: int = 0
        self.avg_doc_len: float = 0.0
        self.total_doc_len: int = 0

        # IDF 缓存
        self._idf_cache: dict[str, float] = {}

    def build_index(self, products: list[dict]) -> None:
        """
        从商品列表构建 BM25 索引

        Args:
            products: 商品字典列表，每个需包含 id, name, description 等字段
        """
        tokenizer = get_tokenizer()
        self.inverted_index = defaultdict(list)
        self.documents = {}
        self._idf_cache = {}

        for product in products:
            product_id = product["id"]
            text = self._product_to_text(product)
            tokens = tokenizer.tokenize(text)

            doc = BM25Document(product_id=product_id, tokens=tokens)
            self.documents[product_id] = doc

            # 更新倒排索引
            for term, tf in doc.token_freq.items():
                self.inverted_index[term].append((product_id, tf))

        # 更新统计
        self.doc_count = len(self.documents)
        self.total_doc_len = sum(doc.doc_len for doc in self.documents.values())
        self.avg_doc_len = self.total_doc_len / self.doc_count if self.doc_count > 0 else 0

        logger.info(f"BM25 index built: {self.doc_count} docs, {len(self.inverted_index)} terms, avg_len={self.avg_doc_len:.1f}")

    def add_product(self, product: dict) -> None:
        """增量添加商品"""
        tokenizer = get_tokenizer()
        product_id = product["id"]
        text = self._product_to_text(product)
        tokens = tokenizer.tokenize(text)

        doc = BM25Document(product_id=product_id, tokens=tokens)
        self.documents[product_id] = doc

        for term, tf in doc.token_freq.items():
            self.inverted_index[term].append((product_id, tf))

        # 更新统计
        self.doc_count = len(self.documents)
        self.total_doc_len += doc.doc_len
        self.avg_doc_len = self.total_doc_len / self.doc_count
        self._idf_cache = {}

    def remove_product(self, product_id: int) -> None:
        """增量删除商品"""
        if product_id not in self.documents:
            return

        doc = self.documents.pop(product_id)

        # 从倒排索引中移除
        for term in doc.token_freq:
            if term in self.inverted_index:
                self.inverted_index[term] = [
                    (pid, tf) for pid, tf in self.inverted_index[term]
                    if pid != product_id
                ]
                if not self.inverted_index[term]:
                    del self.inverted_index[term]

        # 更新统计
        self.doc_count = len(self.documents)
        self.total_doc_len -= doc.doc_len
        self.avg_doc_len = self.total_doc_len / self.doc_count if self.doc_count > 0 else 0
        self._idf_cache = {}

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        """
        BM25 搜索

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果

        Returns:
            [(product_id, score), ...] 按分数降序排列
        """
        if not query or not self.documents:
            return []

        tokenizer = get_tokenizer()
        query_tokens = tokenizer.tokenize(query)

        if not query_tokens:
            return []

        # 计算每个文档的 BM25 分数
        scores: dict[int, float] = defaultdict(float)

        for token in query_tokens:
            idf = self._get_idf(token)
            if idf <= 0:
                continue

            postings = self.inverted_index.get(token, [])
            for product_id, tf in postings:
                doc = self.documents.get(product_id)
                if not doc:
                    continue

                # BM25 公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc.doc_len / self.avg_doc_len)
                scores[product_id] += idf * numerator / denominator

        # 排序并返回 top_k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def _get_idf(self, term: str) -> float:
        """计算 IDF（带缓存）"""
        if term in self._idf_cache:
            return self._idf_cache[term]

        n = len(self.inverted_index.get(term, []))
        N = self.doc_count

        if N == 0 or n == 0:
            idf = 0.0
        else:
            idf = math.log((N - n + 0.5) / (n + 0.5) + 1)

        self._idf_cache[term] = idf
        return idf

    @staticmethod
    def _product_to_text(product: dict) -> str:
        """将商品信息转为可索引文本"""
        parts = [
            product.get("name", ""),
            product.get("description", ""),
        ]
        brand = product.get("brand", "")
        if brand:
            parts.append(brand)
        specs = product.get("specs") or {}
        if specs:
            parts.extend(f"{k}：{v}" for k, v in specs.items())
        return " ".join(parts)


# 全局单例
_bm25_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    """获取 BM25 索引单例"""
    global _bm25_index
    if _bm25_index is None:
        from config import RAG_BM25_K1, RAG_BM25_B
        _bm25_index = BM25Index(k1=RAG_BM25_K1, b=RAG_BM25_B)
    return _bm25_index
