# 🛒 E-Commerce API

基于 **FastAPI + SQLAlchemy 2.0 + Redis + AI** 构建的全功能电商后端 API。

## ✨ 项目亮点

| 特性 | 说明 |
|------|------|
| **JWT 认证** | 用户注册/登录，基于角色的权限控制（普通用户/管理员） |
| **Redis 购物车** | 使用 Redis Hash 存储购物车，支持高并发读写 |
| **订单状态机** | 状态转移表集中管理，防止非法状态变更 |
| **防超卖设计** | WHERE 条件扣减库存，避免并发超卖 |
| **数据快照** | 订单项存储商品快照，历史数据不受商品修改影响 |
| **AI 智能客服** | RAG 检索增强生成，语义搜索，商品推荐 |
| **降级策略** | AI 不可用时自动回退到关键词搜索 |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│                   (HTML/CSS/JS)                         │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────────────────┐
│                    FastAPI                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │  Auth   │ │Products │ │  Cart   │ │ Orders  │      │
│  │ Router  │ │ Router  │ │ Router  │ │ Router  │      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      │
│       │           │           │           │            │
│  ┌────▼───────────▼───────────▼───────────▼────┐      │
│  │              Service Layer                   │      │
│  └────┬───────────┬───────────┬───────────┬────┘      │
└───────┼───────────┼───────────┼───────────┼────────────┘
        │           │           │           │
   ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
   │  MySQL  │ │  Redis  │ │ OpenAI  │ │  JWT    │
   │         │ │         │ │   API   │ │         │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架，自动生成 OpenAPI 文档 |
| SQLAlchemy 2.0 | ORM，异步支持 |
| MySQL | 主数据库 |
| Redis | 购物车存储、缓存 |
| python-jose | JWT 令牌生成与验证 |
| passlib + bcrypt | 密码加密 |
| OpenAI API | AI 智能客服（RAG） |

## 📦 功能模块

### 用户认证
- 用户注册、登录
- JWT 令牌认证
- 角色权限控制（用户/管理员）

### 商品管理
- 商品 CRUD（创建、读取、更新、删除）
- 分页查询、关键词搜索
- 软删除（标记删除而非物理删除）

### 购物车
- 添加、修改、删除商品
- Redis Hash 存储，高性能读写
- 清空购物车

### 订单系统
- 创建订单（库存扣减）
- 订单状态机（待支付→已支付→已发货→已完成/已取消）
- 数据快照（历史订单不受商品修改影响）

### 后台管理
- 用户管理（启用/禁用）
- 订单管理（发货/退款）
- 销售数据统计

### AI 智能客服
- RAG 问答（基于商品数据的检索增强生成）
- 语义搜索（理解用户意图）
- 商品推荐（基于相似度）
- 降级策略（AI 不可用时回退到关键词搜索）

## 🚀 快速开始

### 环境要求

- Python 3.9+
- MySQL 5.7+
- Redis（可选，购物车功能需要）

### 1. 克隆项目

```bash
git clone https://github.com/axlumen/ecommerce-api.git
cd ecommerce-api
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

编辑 `config.py`，修改数据库连接信息：

```python
MYSQL_USER = "root"
MYSQL_PASSWORD = "你的密码"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "ecommerce"
```

### 5. 启动 Redis（可选）

```bash
redis-server
```

### 6. 启动应用

```bash
python -m uvicorn main:app --reload
```

### 7. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

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
| GET | `/api/products` | 商品列表（分页、搜索） |
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
| DELETE | `/api/cart` | 清空购物车 |

### 订单
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/orders` | 创建订单 |
| GET | `/api/orders` | 我的订单列表 |
| GET | `/api/orders/{id}` | 订单详情 |
| PUT | `/api/orders/{id}/cancel` | 取消订单 |
| PUT | `/api/orders/{id}/pay` | 支付订单（模拟） |
| PUT | `/api/orders/{id}/confirm` | 确认收货 |

### 后台管理（需要管理员权限）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/{id}/status` | 禁用/启用用户 |
| GET | `/api/admin/orders` | 所有订单 |
| PUT | `/api/admin/orders/{id}/ship` | 发货 |
| PUT | `/api/admin/orders/{id}/refund` | 退款 |
| GET | `/api/admin/stats/sales` | 销售统计 |
| GET | `/api/admin/stats/users` | 用户统计 |

### AI 智能客服（需要 OPENAI_API_KEY）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | 智能客服问答（RAG） |
| POST | `/api/ai/search` | 语义搜索 |
| GET | `/api/ai/recommend/{product_id}` | 商品推荐 |
| GET | `/api/ai/status` | AI 服务状态 |

## 📁 项目结构

```
ecommerce-api/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置文件
├── database.py             # 数据库连接
├── dependencies.py         # 依赖注入
├── models/                 # SQLAlchemy 数据模型
│   ├── user.py             # 用户模型
│   ├── product.py          # 商品模型
│   ├── order.py            # 订单模型
│   └── cart.py             # 购物车模型
├── schemas/                # Pydantic 数据验证
│   ├── user.py             # 用户 Schema
│   ├── product.py          # 商品 Schema
│   ├── order.py            # 订单 Schema
│   └── cart.py             # 购物车 Schema
├── routers/                # API 路由
│   ├── auth.py             # 认证路由
│   ├── products.py         # 商品路由
│   ├── cart.py             # 购物车路由
│   ├── orders.py           # 订单路由
│   ├── admin.py            # 后台管理路由
│   └── ai.py               # AI 智能客服路由
└── services/               # 业务逻辑层
    ├── auth_service.py     # 认证服务
    ├── product_service.py  # 商品服务
    ├── cart_service.py     # 购物车服务
    ├── order_service.py    # 订单服务
    └── ai_service.py       # AI 服务（RAG、语义搜索、推荐）
```

## 🔧 设计决策

1. **数据快照**：订单项存储商品快照，历史订单不受商品修改影响
2. **状态机**：订单状态用转移表集中管理，防止非法状态变更
3. **防超卖**：WHERE 条件扣减库存，避免并发超卖
4. **签名验证**：支付回调验签防止伪造
5. **幂等性**：重复回调只处理一次
6. **RAG 智能客服**：基于商品数据的检索增强生成，减少幻觉
7. **语义搜索**：理解用户意图，不只是关键词匹配
8. **降级策略**：AI 不可用时自动回退到关键词搜索

## 📄 License

MIT License

## 👨‍💻 作者

- GitHub: [@axlumen](https://github.com/axlumen)
