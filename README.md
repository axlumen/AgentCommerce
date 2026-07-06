# 🛒 AgentCommerce — AI 智能导购电商平台

基于 **FastAPI + LangGraph + RAG + Redis + MySQL** 构建的全功能电商后端 API，集成 AI 智能导购 Agent、三级混合检索、语义缓存、全链路监控。

## ✨ 项目亮点

| 特性 | 说明 |
|------|------|
| **AI 智能导购** | LangGraph ReAct Agent，自动搜索、比价、库存校验、加购，支持多轮对话 |
| **三级混合检索** | BM25 关键词 + FAISS 向量 + Cross-Encoder Reranker，精准匹配商品 |
| **语义缓存** | Redis 存储 query embedding → 答案，相似度 ≥ 0.9 直接返回，延迟 <10ms |
| **全链路监控** | AI 调用日志（token/耗时/模型）、Agent 决策追踪、Redis 统计指标 |
| **限流熔断** | 滑动窗口限流（30次/分钟/用户）、三状态熔断器自动降级 |
| **记忆系统** | 短期滑动窗口（当前对话）+ 长期用户偏好（品类/品牌/价格区间） |
| **安全控制** | 工具权限分级、Prompt 注入检测、敏感操作确认、参数校验 |
| **防超卖设计** | WHERE 条件扣减库存，数据快照保护历史订单 |
| **深色模式** | 前端支持一键切换深色/浅色主题 |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ 商品浏览  │ │ 购物车   │ │ 订单管理  │ │ AI 聊天悬浮窗  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                      FastAPI                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │
│  │  Auth  │ │Products│ │  Cart  │ │ Orders │ │  Agent   │ │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘ │
│      │          │          │          │            │        │
│  ┌───▼──────────▼──────────▼──────────▼────────────▼─────┐ │
│  │                   Service Layer                        │ │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │ │
│  │  │ Agent   │ │   RAG    │ │ Monitor  │ │   Cache   │ │ │
│  │  │ (React) │ │ (Hybrid) │ │ (Logger) │ │ (Semantic)│ │ │
│  │  └─────────┘ └──────────┘ └──────────┘ └───────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└───────┬──────────┬──────────┬──────────┬────────────────────┘
        │          │          │          │
   ┌────▼────┐ ┌───▼────┐ ┌──▼───┐ ┌───▼─────┐
   │  MySQL  │ │ Redis  │ │OpenAI│ │   FAISS │
   │         │ │(cache/ │ │ API  │ │(vectors)│
   │         │ │ratelmt)│ │      │ │         │
   └─────────┘ └────────┘ └──────┘ └─────────┘
```

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架，自动生成 OpenAPI 文档 |
| **SQLAlchemy 2.0** | ORM，MySQL 连接池 |
| **MySQL** | 主数据库（商品/用户/订单） |
| **Redis** | 购物车、语义缓存、限流、熔断器、统计指标 |
| **LangGraph** | Agent 编排框架（ReAct 循环 + human-in-the-loop） |
| **LangChain OpenAI** | LLM 调用 + Embedding 生成 |
| **FAISS** | 向量检索（IndexFlatIP，余弦相似度） |
| **sentence-transformers** | Cross-Encoder Reranker（ms-marco-MiniLM-L6-v2） |
| **jieba** | 中文分词 + 同义词扩展 |
| **python-jose + bcrypt** | JWT 认证 + 密码加密 |

## 📦 功能模块

### 用户认证
- 用户注册、登录，JWT 令牌认证
- 角色权限控制（普通用户/管理员）

### 商品管理
- 商品 CRUD，分页查询，关键词搜索
- 支持品牌、规格参数（JSON 字段）
- 软删除（下架而非物理删除）

### 购物车
- Redis Hash 存储，高性能读写
- 添加、修改、删除、清空

### 订单系统
- 创建订单自动扣减库存（WHERE 条件防超卖）
- 状态机：待支付 → 已支付 → 已发货 → 已完成/已取消
- 数据快照保护历史订单

### 后台管理
- 用户管理（启用/禁用）
- 订单管理（发货/退款）
- 销售数据统计

### AI 智能导购 Agent
- **ReAct 推理**：思考 → 行动 → 观察 → 再思考循环
- **6 个业务工具**：搜索商品、查看详情、校验库存、计算价格、加购、获取偏好
- **Human-in-the-loop**：敏感操作（加购）通过 interrupt 机制暂停等待确认
- **记忆系统**：Redis 短期滑动窗口 + 长期用户偏好提取
- **安全控制**：工具权限分级、Prompt 注入检测、参数校验

### RAG 三级混合检索
- **第一层 BM25**：jieba 中文分词 + 倒排索引 + 同义词扩展
- **第二层向量**：FAISS IndexFlatIP + OpenAI/Sentence-Transformers 嵌入
- **第三层 Reranker**：Cross-Encoder ms-marco-MiniLM-L6-v2 重排序
- **融合策略**：min-max 归一化 + 加权融合（α=0.3, β=0.3, γ=0.4）
- **降级链**：全量 → BM25+Vector → BM25 only → MySQL LIKE

### 语义缓存
- Redis 存储 query embedding → 缓存答案
- 余弦相似度 ≥ 0.9 直接返回（延迟 <10ms）
- 商品更新自动清除相关缓存
- 命中率统计

### 全链路监控
- AI 调用日志：模型、token 数、耗时、成功/失败
- Agent 决策追踪：每步思考、工具调用、结果
- Redis 统计计数器：总调用、成功率、平均延迟、token 消耗

### 限流与熔断
- 滑动窗口限流：Redis ZSET，每用户每分钟 30 次
- 三状态熔断器：CLOSED → OPEN（连续 5 次失败）→ HALF_OPEN（60s 后试探）→ CLOSED
- 降级回退：熔断时自动降级到关键词搜索

### 前端 UI
- 深色模式一键切换
- AI 智能导购悬浮聊天窗（浮动气泡 + 对话窗口）
- 商品卡片（品牌标签、销量徽章、悬停动画）
- 响应式设计（768px / 480px 断点）

## 🚀 快速开始

### Docker 一键部署（推荐）

```bash
git clone https://github.com/axlumen/AgentCommerce.git
cd AgentCommerce
docker-compose up -d --build
```

启动后访问：
- 前端页面：http://localhost:8000
- API 文档：http://localhost:8000/docs

```bash
docker-compose logs -f app   # 查看应用日志
docker-compose down           # 停止服务
docker-compose down -v        # 停止并删除数据卷（MySQL 数据会丢失）
```

> 包含三个服务：App（FastAPI）+ MySQL 8.0 + Redis 7，数据库自动初始化。

导入种子数据（可选，35 个演示商品）：

```bash
docker-compose exec app python -m scripts.seed_data
```

---

### 手动部署

#### 环境要求

- Python 3.10+
- MySQL 5.7+
- Redis 6.0+

#### 1. 克隆项目

```bash
git clone https://github.com/axlumen/AgentCommerce.git
cd AgentCommerce
```

#### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置数据库

```sql
CREATE DATABASE agentcommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

通过环境变量配置（或直接编辑 `config.py`）：

```bash
# Windows
set MYSQL_PASSWORD=你的密码
set SECRET_KEY=你的密钥
set OPENAI_API_KEY=sk-xxx

# Linux/Mac
export MYSQL_PASSWORD=你的密码
export SECRET_KEY=你的密钥
export OPENAI_API_KEY=sk-xxx
```

#### 5. 启动 Redis

```bash
redis-server
```

#### 6. 初始化种子数据（可选）

```bash
python -m scripts.seed_data
```

> 包含 35 个热销商品（手机、耳机、笔记本、手表、家电），用于演示和测试。

#### 6. 启动应用

```bash
python -m uvicorn main:app --reload
```

#### 7. 访问

- 前端页面：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 📚 API 接口

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 商品
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products` | 商品列表（分页、搜索、排序） |
| GET | `/api/products/{id}` | 商品详情 |
| POST | `/api/products` | 创建商品 |
| PUT | `/api/products/{id}` | 更新商品 |
| DELETE | `/api/products/{id}` | 删除商品（软删除） |

### 购物车
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cart` | 获取购物车 |
| POST | `/api/cart` | 添加到购物车 |
| PUT | `/api/cart/{product_id}` | 更新数量 |
| DELETE | `/api/cart/{product_id}` | 删除商品 |

### 订单
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/orders` | 创建订单 |
| GET | `/api/orders` | 我的订单列表 |
| PUT | `/api/orders/{id}/pay` | 支付订单 |
| PUT | `/api/orders/{id}/cancel` | 取消订单 |
| PUT | `/api/orders/{id}/confirm` | 确认收货 |

### 后台管理（需要管理员权限）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表 |
| GET | `/api/admin/orders` | 所有订单 |
| PUT | `/api/admin/orders/{id}/ship` | 发货 |
| PUT | `/api/admin/orders/{id}/refund` | 退款 |
| GET | `/api/admin/stats/sales` | 销售统计 |

### AI 智能客服
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | RAG 问答（三级检索 + 语义缓存） |
| POST | `/api/ai/search` | 语义搜索 |
| GET | `/api/ai/recommend/{id}` | 商品推荐 |
| GET | `/api/ai/status` | 服务状态（RAG/缓存/熔断器） |
| GET | `/api/ai/stats` | AI 调用统计指标 |

### AI 智能导购 Agent
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/chat` | Agent 对话（ReAct 模式，自动调用工具） |
| POST | `/api/agent/confirm` | 确认敏感操作（加购等） |
| GET | `/api/agent/history/{session_id}` | 对话历史 |
| DELETE | `/api/agent/history/{session_id}` | 清除对话历史 |
| GET | `/api/agent/preferences` | 用户偏好 |
| GET | `/api/agent/stats` | Agent 统计（含缓存/熔断器） |

## 📁 项目结构

```
AgentCommerce/
├── main.py                     # FastAPI 入口 + RAG 索引构建 + 请求日志中间件
├── config.py                   # 配置（环境变量读取）
├── database.py                 # MySQL 连接池
├── redis_client.py             # 共享 Redis 客户端
├── dependencies.py             # JWT 认证依赖注入
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # 一键部署（App + MySQL + Redis）
├── .dockerignore               # Docker 构建排除规则
│
├── agent/                      # AI 智能导购 Agent（7 文件，1578 行）
│   ├── state.py                #   Agent 状态定义
│   ├── tools.py                #   6 个业务工具（上下文变量传递 DB）
│   ├── graph.py                #   LangGraph ReAct 图（并行工具执行）
│   ├── llm.py                  #   LLM 客户端管理（缓存单例）
│   ├── prompts.py              #   提示词与消息构建
│   ├── memory.py               #   记忆系统（短期/长期）
│   └── security.py             #   安全控制（权限/注入/校验）
│
├── rag/                        # RAG 三级混合检索（9 文件，1785 行）
│   ├── tokenizer.py            #   jieba 分词 + 同义词扩展
│   ├── bm25.py                 #   第一层：BM25 倒排索引
│   ├── vector_store.py         #   第二层：FAISS 向量检索
│   ├── reranker.py             #   第三层：Cross-Encoder 重排序
│   ├── retriever.py            #   三级融合检索器
│   ├── chunker.py              #   结构化商品分块
│   ├── evaluation.py           #   评估框架（Recall/NDCG/Precision）
│   └── exceptions.py           #   自定义异常
│
├── monitoring/                 # 监控模块（4 文件，667 行）
│   ├── logger.py               #   AI 调用日志 + Agent 追踪 + 统计
│   ├── rate_limiter.py         #   滑动窗口限流（Redis ZSET）
│   └── circuit_breaker.py      #   三状态熔断器
│
├── cache/                      # 缓存模块（2 文件，343 行）
│   └── semantic_cache.py       #   语义缓存（embedding 相似度）
│
├── frontend/                   # 前端（3 文件，2046 行）
│   ├── index.html              #   单页应用 + AI 聊天悬浮窗
│   ├── style.css               #   深色模式 + 响应式 + 聊天窗样式
│   └── app.js                  #   API 调用 + AI 聊天 + 主题切换
│
├── models/                     # SQLAlchemy 数据模型
├── schemas/                    # Pydantic 数据验证
├── routers/                    # API 路由
├── services/                   # 业务逻辑层
├── data/                       # 测试集 + 索引文件
│   └── test_set.json           #   50 条评估问答对
└── scripts/
    ├── seed_data.py            #   商品种子数据（35 个热销商品）
    └── run_evaluation.py       #   RAG 评估脚本
```

## 🔧 设计决策

| # | 决策 | 说明 |
|---|------|------|
| 1 | **数据快照** | 订单项存储商品快照，历史订单不受商品修改影响 |
| 2 | **状态机** | 订单状态用转移表集中管理，防止非法状态变更 |
| 3 | **防超卖** | WHERE 条件扣减库存，避免并发超卖 |
| 4 | **ReAct Agent** | LangGraph 实现思考→行动→观察循环，支持多工具编排 |
| 5 | **Human-in-the-loop** | 敏感操作（加购）通过 interrupt 暂停，等待用户确认 |
| 6 | **三级检索融合** | BM25(0.3) + Vector(0.3) + Reranker(0.4) 加权融合 |
| 7 | **同义词扩展** | 电商同义词表（手机=智能手机=移动电话），提升召回率 |
| 8 | **语义缓存** | embedding 余弦相似度 ≥ 0.9 返回缓存，商品更新自动失效 |
| 9 | **熔断器** | 连续 5 次失败 → OPEN，60s 后 HALF_OPEN 试探，成功 → CLOSED |
| 10 | **并行工具执行** | ThreadPoolExecutor + contextvars.copy_context() 并行调用多个工具 |
| 11 | **降级链** | 全量混合检索 → BM25+Vector → BM25 only → MySQL LIKE |

## 📊 代码统计

| 模块 | 文件数 | 行数 |
|------|--------|------|
| rag/ | 9 | 1785 |
| agent/ | 7 | 1578 |
| frontend/ | 3 | 2046 |
| routers/ | 8 | 1178 |
| services/ | 6 | 818 |
| monitoring/ | 4 | 667 |
| cache/ | 2 | 343 |
| models/ + schemas/ | 10 | 379 |
| 其他 | 4 | 440 |
| **合计** | **53** | **~9200** |

## 📄 License

MIT License

## 👨‍💻 作者

- GitHub: [@axlumen](https://github.com/axlumen)
