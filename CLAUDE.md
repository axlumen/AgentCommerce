# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 智能导购电商平台，Next.js 16 前端 + FastAPI 后端，集成 LangGraph Agent、三级 RAG 检索、语义缓存。

## 常用命令

### 后端

```bash
# 启动开发服务器（热重载）
uvicorn main:app --reload

# 安装依赖
pip install -r requirements.txt

# 导入种子数据（77 个中文演示商品，覆盖美妆/香水/家具/食品/家居/厨房 6 大品类）
python -m scripts.seed_data
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（Turbopack）
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 访问地址

- 前端：http://localhost:3000（开发）/ http://localhost:8000（生产）
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 环境配置

项目使用 `.env` 文件（本地开发）或环境变量配置。关键变量见 `config.py`：

- `MYSQL_*` / `DATABASE_URL` — MySQL 连接（默认 `root:123456@localhost:3306/agentcommerce`）
- `REDIS_*` — Redis 连接（默认 `localhost:6379`）
- `SECRET_KEY` — JWT 签名密钥
- `OPENAI_API_KEY` — LLM 调用
- `DASHSCOPE_API_KEY` — 通义千问 Embedding（默认 provider）
- `AGENT_MODEL` — Agent 使用的模型（默认 `mimo-v2.5-pro`）
- `RAG_EMBEDDING_PROVIDER` — Embedding 提供商（`openai` / `dashscope` / `local`）

## 架构

### 整体结构

```
frontend/          Next.js 16 + TypeScript + Tailwind + shadcn/ui
routers/           FastAPI 路由层（请求分发、参数校验）
services/          业务逻辑层
models/            SQLAlchemy ORM 模型
schemas/           Pydantic 数据验证
agent/             LangGraph ReAct Agent
rag/               三级混合检索（BM25 + FAISS + Reranker）
monitoring/        限流 + 熔断 + 日志
cache/             语义缓存
scripts/           种子数据（77 个中文商品）
```

### 前端架构

- **App Router**（`frontend/app/`）：页面路由，每页一个 `page.tsx`
- **组件**（`frontend/components/`）：`ui/` 放 shadcn 基础组件，`layout/` 放 Header/Footer，`product/` 放商品相关，`chat/` 放 AI 聊天窗
- **状态管理**（`frontend/store/`）：Zustand stores — `auth.ts`（用户认证）、`cart.ts`（购物车）、`ui.ts`（UI 状态）
- **Hooks**（`frontend/hooks/`）：`useAuth`（登录/注册/登出）、`useCart`（购物车操作）
- **工具**（`frontend/lib/`）：`api.ts`（后端 API 客户端）、`utils.ts`（格式化函数）、`query-client.ts`（TanStack Query 配置）
- **主题**：通过 `next-themes` 实现深色模式，`Providers.tsx` 包装全局 Provider
- **Markdown 渲染**：`react-markdown` + `remark-gfm`（支持 GFM 表格），`chat/ChatWidget.tsx` 中配置

### 后端关键模块

**`agent/`** — LangGraph ReAct Agent（AI 智能导购）
- `graph.py` — ReAct 循环图定义（思考→行动→观察），支持并行工具执行
- `tools.py` — 6 个业务工具（搜索/详情/库存/价格/加购/偏好），通过 contextvars 传递 DB session
- `memory.py` — 短期滑动窗口 + 长期用户偏好提取（Redis 存储）
- `security.py` — 工具权限分级、Prompt 注入检测、参数校验

**`rag/`** — 三级混合检索系统
- `bm25.py` — 第一层：jieba 分词 + BM25 倒排索引
- `vector_store.py` — 第二层：FAISS 向量检索（支持 OpenAI/DashScope/本地 embedding）
- `reranker.py` — 第三层：Cross-Encoder ms-marco-MiniLM-L6-v2 重排序
- `retriever.py` — 三级融合（α=0.3, β=0.3, γ=0.4）+ 降级链

**`monitoring/`** — 监控与限流
- `rate_limiter.py` — Redis ZSET 滑动窗口限流（30 次/分钟/用户）
- `circuit_breaker.py` — 三状态熔断器（CLOSED→OPEN→HALF_OPEN）

**`cache/`** — 语义缓存（embedding 余弦相似度 ≥ 0.9 直接返回）

### 请求流程

1. 浏览器访问 `localhost:3000`（Next.js 开发服务器）
2. 前端通过 `frontend/lib/api.ts` 调用 `localhost:8000/api/*` 接口（开发环境由 `next.config.ts` 的 rewrites 代理）
3. `main.py` 中间件记录请求耗时
4. Router → Service → Model（SQLAlchemy）→ MySQL
5. Agent 请求：Router → `agent/graph.py`（LangGraph ReAct 循环）→ 工具调用 → 返回

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

### Python（后端）

- Python 3.10+，使用类型注解
- Router 函数保持简洁，复杂逻辑放 `services/`
- Agent 工具函数通过 `contextvars` 获取 DB session（见 `agent/tools.py`）
- 配置集中在 `config.py`，通过环境变量覆盖默认值

### TypeScript（前端）

- **Next.js 16 有破坏性变更**，写前端代码前先读 `frontend/node_modules/next/dist/docs/` 中的指南
- 组件用函数式 + Hooks，不用 class
- shadcn/ui 组件放在 `components/ui/`，不要修改，直接用 `npx shadcn@latest add <component>` 添加
- 业务状态用 Zustand（`store/`），服务端数据用 TanStack Query（`lib/query-client.ts`）
- API 调用统一走 `lib/api.ts`，不要在组件里直接 fetch
- 样式用 Tailwind CSS，不要写自定义 CSS（`globals.css` 除外）

## Docker 部署（推荐）

```bash
docker-compose up -d --build       # 构建并启动（App + MySQL + Redis）
docker-compose exec app python -m scripts.seed_data  # 导入种子数据
docker-compose logs -f app         # 查看日志
docker-compose down                # 停止
docker-compose down -v             # 停止并删除数据卷（MySQL 数据会丢失）
```

- 前端页面：http://localhost:8000
- API 文档：http://localhost:8000/docs

Docker 架构：Nginx（:80）→ `/` 转发 Next.js standalone server（:3000），`/api/` 转发 Uvicorn（:8000）。Supervisor 管理三个进程。

## 前置依赖（手动部署）

本地开发需要运行：
- **MySQL 8.0+** — 创建数据库 `agentcommerce`（UTF-8）
- **Redis 6.0+** — 默认 `localhost:6379`

首次启动后访问 `http://localhost:8000/docs` 验证后端正常，运行 `python -m scripts.seed_data` 导入演示数据（77 个中文商品，覆盖美妆护肤、香水香氛、家具家居、食品生鲜、家居装饰、厨房用品 6 个品类）。
