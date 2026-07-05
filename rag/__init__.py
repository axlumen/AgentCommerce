"""
RAG 检索增强生成模块

三级混合检索架构：
- 第一层：BM25 关键词检索（jieba 分词 + 倒排索引）
- 第二层：向量语义检索（FAISS + OpenAI/Sentence-Transformers 嵌入）
- 第三层：Reranker 重排（Cross-Encoder）
"""
