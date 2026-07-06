"""
项目配置

敏感配置通过环境变量读取，有默认值用于本地开发。
生产环境务必设置环境变量。
"""

import os
from pathlib import Path

# 加载 .env 文件（本地开发用，Docker 环境通过 env_file 加载）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass  # python-dotenv 未安装时跳过

# MySQL 配置
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agentcommerce")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4",
)

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时

# 购物车配置
CART_KEY_PREFIX = "cart:"
CART_EXPIRE_DAYS = 7  # 购物车 7 天过期

# 订单配置
ORDER_TIMEOUT_MINUTES = 30  # 订单 30 分钟未支付自动取消

# Agent 配置
AGENT_MODEL = os.getenv("AGENT_MODEL", "mimo-v2.5-pro")
AGENT_MAX_ITERATIONS = 10
AGENT_TOOL_TIMEOUT = 30
AGENT_CONTEXT_WINDOW = 20
AGENT_SESSION_TTL = 7200

# RAG 检索配置
RAG_BM25_K1 = 1.5
RAG_BM25_B = 0.75
RAG_ALPHA = 0.3
RAG_BETA = 0.3
RAG_GAMMA = 0.4
RAG_TOP_K_BM25 = 20
RAG_TOP_K_VECTOR = 20
RAG_TOP_K_FINAL = 5

# Embedding 模型配置
# 支持: "text-embedding-3-small" (OpenAI), "qwen3-vl-embedding" (通义千问), "all-MiniLM-L6-v2" (本地)
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-vl-embedding")
RAG_EMBEDDING_DIMENSION = int(os.getenv("RAG_EMBEDDING_DIMENSION", "1024"))  # qwen3-vl-embedding 维度
RAG_EMBEDDING_PROVIDER = os.getenv("RAG_EMBEDDING_PROVIDER", "dashscope")  # openai, dashscope, local

# 通义千问 DashScope 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

RAG_RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")
RAG_FAISS_INDEX_PATH = "data/faiss_index.bin"
RAG_SYNONYM_PATH = "data/synonyms.json"

# 语义缓存配置
CACHE_SEMANTIC_ENABLED = True
CACHE_SIMILARITY_THRESHOLD = 0.9
CACHE_TTL = 3600
CACHE_MAX_ENTRIES = 10000

# 限流配置
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# 熔断器配置
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
