# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 智能导购电商平台，基于 FastAPI + LangGraph + RAG + Redis + MySQL 构建。

## 常用命令

```bash
# 启动开发服务器（热重载）
uvicorn main:app --reload

# 安装依赖
pip install -r requirements.txt

# 导入种子数据（35 个演示商品）
python -m scripts.seed_data

# RAG 评估脚本
python -m scripts.run_evaluation
```

**访问地址：**
- 前端页面：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 环境配置

项目使用 `.env` 文件（本地开发）或环境变量配置。关键变量见 `config.py`：

- `MYSQL_*` / `DATABASE_URL` — MySQL 连接
- `REDIS_*` — Redis 连接
- `SECRET_KEY` — JWT 签名密钥
- `OPENAI_API_KEY` — LLM 调用
- `DASHSCOPE_API_KEY` — 通义千问 Embedding（默认 provider）
- `AGENT_MODEL` — Agent 使用的模型（默认 `mimo-v2.5-pro`）
- `RAG_EMBEDDING_PROVIDER` — Embedding 提供商（`openai` / `dashscope` / `local`）

## 架构

### 核心分层

```
routers/  → 路由层（请求分发、参数校验）
services/ → 业务逻辑层
models/   → SQLAlchemy ORM 模型
schemas/  → Pydantic 数据验证
```

### 关键模块

**`agent/`** — LangGraph ReAct Agent（AI 智能导购）
- `graph.py` — ReAct 循环图定义（思考→行动→观察），支持并行工具执行
- `tools.py` — 6 个业务工具（搜索/详情/库存/价格/加购/偏好），通过 contextvars 传递 DB session
- `memory.py` — 短期滑动窗口 + 长期用户偏好提取（Redis 存储）
- `security.py` — 工具权限分级、Prompt 注入检测、参数校验
- `prompts.py` — 系统提示词与消息构建

**`rag/`** — 三级混合检索系统
- `bm25.py` — 第一层：jieba 分词 + BM25 倒排索引
- `vector_store.py` — 第二层：FAISS 向量检索（支持 OpenAI/DashScope/本地 embedding）
- `reranker.py` — 第三层：Cross-Encoder ms-marco-MiniLM-L6-v2 重排序
- `retriever.py` — 三级融合（α=0.3, β=0.3, γ=0.4）+ 降级链
- `tokenizer.py` — jieba 分词 + 电商同义词扩展

**`monitoring/`** — 监控与限流
- `rate_limiter.py` — Redis ZSET 滑动窗口限流（30 次/分钟/用户）
- `circuit_breaker.py` — 三状态熔断器（CLOSED→OPEN→HALF_OPEN）

**`cache/`** — 语义缓存（embedding 余弦相似度 ≥ 0.9 直接返回）

### 请求流程

1. 前端 `frontend/app.js` 调用 `/api/*` 接口
2. `main.py` 中间件记录请求耗时
3. Router → Service → Model（SQLAlchemy）→ MySQL
4. Agent 请求：Router → `agent/graph.py`（LangGraph ReAct 循环）→ 工具调用 → 返回

### 数据库

- SQLAlchemy 2.0，`database.py` 定义 engine/session
- `create_tables()` 在应用启动时自动建表（`main.py` lifespan）
- 订单使用数据快照保护历史记录，库存扣减用 WHERE 条件防超卖

### Redis 用途

- 购物车（Hash，7 天过期）
- 语义缓存（embedding → 答案）
- Agent 对话记忆（短期滑动窗口 + 长期偏好）
- 限流计数器（ZSET）
- 熔断器状态

## 代码规范

- Python 3.10+，使用类型注解
- Router 函数保持简洁，复杂逻辑放 `services/`
- Agent 工具函数通过 `contextvars` 获取 DB session（见 `agent/tools.py`）
- 配置集中在 `config.py`，通过环境变量覆盖默认值
- 前端是 Vanilla JS 单页应用（`frontend/` 目录），无需构建工具
