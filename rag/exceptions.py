"""
RAG 模块自定义异常

分级异常处理，确保各层故障可独立降级。
"""


class RAGError(Exception):
    """RAG 基础异常"""
    pass


class BM25IndexError(RAGError):
    """BM25 索引构建或查询异常"""
    pass


class VectorStoreError(RAGError):
    """向量存储异常"""
    pass


class RerankerError(RAGError):
    """Reranker 异常"""
    pass


class EmbeddingError(RAGError):
    """嵌入生成异常"""
    pass


class TokenizerError(RAGError):
    """分词器异常"""
    pass


class EvaluationError(RAGError):
    """评估异常"""
    pass
