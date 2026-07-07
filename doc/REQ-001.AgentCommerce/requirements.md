# 需求说明书 — AgentCommerce

| 字段 | 内容 |
|------|------|
| 需求编号 | REQ-001 |
| 需求名称 | AI 智能导购电商平台 |
| 版本 | v1.1 |
| 日期 | 2026-07-07 |
| 状态 | ✅ 已完成 |

---

## 1. 需求背景

传统电商搜索依赖关键词匹配，无法理解用户自然语言意图，导致：
- 用户需要精确关键词才能找到商品
- 无法进行多条件组合筛选（如"2000元左右的降噪耳机"）
- 缺乏个性化推荐能力

本项目旨在构建一个 **AI Agent 驱动的智能导购电商平台**，通过自然语言交互实现商品搜索、比价、加购等操作。

---

## 2. 功能需求

### 2.1 用户认证模块

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 用户注册 | 用户名 + 密码注册，密码 bcrypt 加密 | P0 |
| 用户登录 | JWT 令牌认证，过期时间可配置 | P0 |
| 角色权限 | 普通用户 / 管理员两级权限 | P0 |
| 获取用户信息 | `/api/auth/me` 返回当前用户 | P1 |

### 2.2 商品管理模块

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 商品列表 | 分页查询，支持关键词搜索、品牌筛选、排序 | P0 |
| 商品详情 | 查看商品完整信息（价格、库存、规格参数） | P0 |
| 商品 CRUD | 管理员创建/更新/删除商品 | P0 |
| 软删除 | 下架而非物理删除，保留数据 | P1 |
| 规格参数 | JSON 字段存储（颜色、尺寸、型号等） | P1 |

### 2.3 购物车模块

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 添加商品 | 将商品加入购物车，支持数量指定 | P0 |
| 修改数量 | 更新购物车商品数量 | P0 |
| 删除商品 | 从购物车移除单个商品 | P0 |
| 清空购物车 | 一键清空所有商品 | P1 |
| 购物车查询 | 返回当前用户购物车列表 | P0 |

**技术约束**：使用 Redis Hash 存储，高性能读写。

### 2.4 订单模块

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 创建订单 | 从购物车生成订单，自动扣减库存 | P0 |
| 订单支付 | 模拟支付，更新订单状态 | P0 |
| 取消订单 | 用户取消订单，恢复库存 | P0 |
| 确认收货 | 用户确认收货，完成订单 | P1 |
| 订单列表 | 查看用户历史订单 | P0 |
| 数据快照 | 订单项存储商品快照，不受商品修改影响 | P1 |

**业务规则**：
- 状态机：`待支付 → 已支付 → 已发货 → 已完成` / `待支付 → 已取消`
- 防超卖：`WHERE stock >= quantity` 条件扣减库存

### 2.5 后台管理模块

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 用户管理 | 查看用户列表，启用/禁用用户 | P1 |
| 订单管理 | 查看所有订单，发货/退款操作 | P0 |
| 销售统计 | 销售额、订单量、热销商品统计 | P1 |

### 2.6 AI 智能导购 Agent（核心功能）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 自然语言对话 | 用户输入自然语言，Agent 理解意图并执行 | P0 |
| ReAct 推理 | 思考 → 行动 → 观察 → 再思考循环 | P0 |
| 工具调用 | 6 个业务工具（搜索、详情、库存、价格、加购、偏好） | P0 |
| 多轮对话 | 保持上下文，支持追问和澄清 | P0 |
| 人工确认 | 敏感操作（加购）暂停等待用户确认 | P0 |
| 记忆系统 | 短期滑动窗口 + 长期用户偏好提取 | P1 |
| 安全控制 | 工具权限分级、Prompt 注入检测、参数校验 | P1 |

**工具列表**：

| 工具名 | 功能 | 权限 |
|--------|------|------|
| `search_products` | 搜索商品 | 只读 |
| `get_product_details` | 获取商品详情 | 只读 |
| `check_stock` | 校验库存 | 只读 |
| `calculate_price` | 计算价格（含优惠） | 只读 |
| `add_to_cart` | 加入购物车 | 写入（需确认） |
| `get_user_preferences` | 获取用户偏好 | 只读 |

### 2.7 RAG 三级混合检索

| 功能 | 描述 | 优先级 |
|------|------|--------|
| BM25 关键词检索 | jieba 中文分词 + 倒排索引 + 同义词扩展 | P0 |
| FAISS 向量检索 | 基于 embedding 的语义相似度检索 | P0 |
| Cross-Encoder Reranker | ms-marco-MiniLM-L6-v2 重排序 | P1 |
| 融合策略 | min-max 归一化 + 加权融合（α=0.3, β=0.3, γ=0.4） | P0 |
| 降级链 | 全量 → BM25+Vector → BM25 only → MySQL LIKE | P1 |

### 2.8 语义缓存

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 缓存存储 | Redis 存储 query embedding → 答案 | P0 |
| 相似度匹配 | 余弦相似度 ≥ 0.9 直接返回缓存 | P0 |
| 自动失效 | 商品更新自动清除相关缓存 | P1 |
| 命中率统计 | 统计缓存命中率 | P2 |

### 2.9 全链路监控

| 功能 | 描述 | 优先级 |
|------|------|--------|
| AI 调用日志 | 记录模型、token 数、耗时、成功/失败 | P0 |
| Agent 决策追踪 | 每步思考、工具调用、结果 | P1 |
| 统计指标 | 总调用、成功率、平均延迟、token 消耗 | P1 |

### 2.10 限流与熔断

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 滑动窗口限流 | Redis ZSET，每用户每分钟 30 次 | P0 |
| 熔断器 | CLOSED → OPEN（连续 5 次失败）→ HALF_OPEN（60s 后）→ CLOSED | P1 |
| 降级回退 | 熔断时自动降级到关键词搜索 | P1 |

### 2.11 前端 UI

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 商品浏览 | 商品卡片展示（品牌标签、销量徽章） | P0 |
| 购物车 | 购物车管理界面 | P0 |
| 订单管理 | 订单列表、状态展示 | P0 |
| AI 聊天悬浮窗 | 浮动气泡 + 对话窗口 | P0 |
| 深色模式 | 一键切换深色/浅色主题 | P2 |
| 响应式设计 | 768px / 480px 断点适配 | P1 |

---

## 3. 非功能需求

### 3.1 性能要求

| 指标 | 目标值 |
|------|--------|
| API 响应时间 | < 200ms（普通接口） |
| AI 对话响应 | < 3s（首 token） |
| 语义缓存命中 | < 10ms |
| 并发支持 | ≥ 100 QPS |

### 3.2 可靠性要求

| 指标 | 目标值 |
|------|--------|
| 服务可用性 | ≥ 99.5% |
| 数据持久化 | MySQL 主从 + 定期备份 |
| 缓存失效 | 自动降级到数据库查询 |

### 3.3 安全要求

| 要求 | 描述 |
|------|------|
| 认证鉴权 | JWT 令牌 + 角色权限控制 |
| 密码安全 | bcrypt 加密存储 |
| 注入防护 | Prompt 注入检测、SQL 参数化 |
| 限流防护 | 每用户每分钟 30 次请求限制 |

### 3.4 可维护性要求

| 要求 | 描述 |
|------|------|
| 代码规范 | PEP 8，类型注解 |
| 日志规范 | 结构化日志，请求链路追踪 |
| 配置管理 | 环境变量 + 配置文件分离 |
| 文档完整 | API 自动生成 OpenAPI 文档 |

---

## 4. 技术方案

### 4.1 技术栈选型

#### 后端

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| Web 框架 | FastAPI | 原生异步、自动 OpenAPI 文档、类型安全 |
| ORM | SQLAlchemy 2.0 | 成熟稳定、连接池管理、支持异步 |
| 数据库 | MySQL 8.0 | 事务支持、成熟生态 |
| 缓存 | Redis 7.0 | 高性能、支持多种数据结构 |
| Agent 框架 | LangGraph | ReAct 模式原生支持、Human-in-the-loop |
| LLM | OpenAI GPT / mimo-v2.5-pro | 多 provider 支持，可通过 `AGENT_MODEL` 配置切换 |
| Embedding | OpenAI / DashScope / 本地 | 三级降级链，通过 `RAG_EMBEDDING_PROVIDER` 配置 |
| 向量库 | FAISS | 轻量级、高性能、无需额外服务 |
| 重排序 | sentence-transformers | Cross-Encoder 效果好 |
| 分词 | jieba | 中文分词标准工具 |

#### 前端

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| 框架 | Next.js 16 (App Router) | SSR/ISR、文件路由、Turbopack 开发体验 |
| 语言 | TypeScript | 类型安全、IDE 支持好 |
| UI 组件库 | shadcn/ui + @base-ui/react | 可定制、无运行时、符合 Radix API 设计 |
| 样式 | Tailwind CSS 4 | 原子化 CSS、零运行时 |
| 状态管理 | Zustand (persist) | 轻量、支持持久化、TypeScript 友好 |
| 服务端数据 | TanStack Query | 缓存、重试、乐观更新 |
| 主题 | next-themes | 深色模式切换 |
| 通知 | sonner | 轻量 toast 组件 |
| HTTP 客户端 | fetch (封装于 lib/api.ts) | 统一错误处理、token 注入 |

### 4.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│              Frontend (Next.js 16 + TypeScript)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ 商品浏览  │ │ 购物车   │ │ 订单管理  │ │ AI 聊天悬浮窗  │ │
│  │(Zustand) │ │(Zustand) │ │(TanStack) │ │   (Zustand)   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (api.ts)
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
│  │  │(LangGrph│ │ (Hybrid) │ │ (Logger) │ │ (Semantic)│ │ │
│  │  └─────────┘ └──────────┘ └──────────┘ └───────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└───────┬──────────┬──────────┬──────────┬────────────────────┘
        │          │          │          │
   ┌────▼────┐ ┌───▼────┐ ┌──▼───┐ ┌───▼─────┐
   │  MySQL  │ │ Redis  │ │ LLM  │ │  FAISS  │
   │         │ │(cache/ │ │ API  │ │(vectors)│
   │         │ │ratelmt)│ │OpenAI│ │DashScope│
   │         │ │        │ │ mimo │ │Embedding│
   └─────────┘ └────────┘ └──────┘ └─────────┘
```

### 4.3 核心设计决策

| # | 决策 | 说明 | 权衡 |
|---|------|------|------|
| 1 | 数据快照 | 订单项存储商品快照 | 空间换一致性 |
| 2 | 状态机 | 订单状态转移表集中管理 | 防止非法状态变更 |
| 3 | 防超卖 | WHERE 条件扣减库存 | 数据库层面保证 |
| 4 | ReAct Agent | 思考→行动→观察循环 | 可解释性 vs 响应速度 |
| 5 | Human-in-the-loop | 敏感操作暂停确认 | 安全性 vs 用户体验 |
| 6 | 三级检索融合 | BM25+Vector+Reranker | 效果 vs 成本 |
| 7 | 语义缓存 | embedding 相似度匹配 | 响应速度 vs 准确性 |
| 8 | 熔断器 | 三状态自动切换 | 可用性 vs 一致性 |
| 9 | 并行工具执行 | ThreadPoolExecutor | 吞吐量 vs 资源消耗 |

### 4.4 数据库设计

**核心表**：

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    brand VARCHAR(50),
    category VARCHAR(50),
    specs JSON,
    sales_count INT DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 订单项表（含数据快照）
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,  -- 快照
    product_price DECIMAL(10,2) NOT NULL, -- 快照
    quantity INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

### 4.5 API 设计

RESTful 风格，统一响应格式：

```json
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
```

分页接口：

```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

---

## 5. 交付标准

### 5.1 功能交付

- √ 用户注册/登录/鉴权
- √ 商品 CRUD + 搜索
- √ 购物车管理
- √ 订单全流程
- √ 后台管理
- √ AI 智能导购 Agent
- √ RAG 三级混合检索
- √ 语义缓存
- √ 全链路监控
- √ 限流熔断
- √ 前端 UI

### 5.2 文档交付

- √ README.md（项目说明 + 部署指南）
- √ API 文档（FastAPI 自动生成）
- √ 需求文档（本文档）
- √ 测试用例（119 条）
- √ 测试报告
- √ SA 代码评审报告

### 5.3 部署交付

- √ Dockerfile
- √ docker-compose.yml
- √ 种子数据脚本

---

## 6. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-07-07 | v1.1 | 补充前端技术栈（Next.js 16、shadcn/ui、Zustand 等）；修复 Button asChild 组件 bug | Claudian |
| 2026-07-06 | v1.0 | 初始版本，基于代码反向梳理 | Claudian |

---

## 关联文档

- [[sa-code-review.md]] — SA 代码评审报告
- [[test-cases.md]] — 测试用例（119 条）
- [[test-report.md]] — 测试报告
