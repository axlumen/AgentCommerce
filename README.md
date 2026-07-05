# 电商 API

一个完整的电商后端 API，基于 FastAPI + SQLAlchemy + Redis + AI 实现。

## 技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM |
| MySQL | 数据库 |
| Redis | 购物车存储 |
| python-jose | JWT 认证 |
| passlib + bcrypt | 密码加密 |
| OpenAI API | AI 智能客服（RAG） |

## 功能模块

| 模块 | 功能 |
|------|------|
| 用户认证 | 注册、登录、JWT |
| 商品管理 | CRUD、分页、搜索、分类 |
| 购物车 | 添加、修改、删除、Redis Hash |
| 订单系统 | 创建、状态机、库存扣减、数据快照 |
| 后台管理 | 用户管理、订单管理、数据统计 |
| **AI 智能客服** | **RAG 问答、语义搜索、商品推荐** |

## 快速开始

### 1. 创建 MySQL 数据库

```sql
CREATE DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 修改配置

编辑 `config.py`，修改 MySQL 连接信息：

```python
MYSQL_USER = "root"
MYSQL_PASSWORD = "你的密码"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "ecommerce"
```

### 3. 安装依赖

```bash
cd "E:\Develop\FastAPIProject\Project examples\ecommerce-api"
pip install -r requirements.txt
```

### 4. 启动 Redis（可选，购物车功能需要）

```bash
redis-server
```

### 5. 启动应用

```bash
python -m uvicorn main:app --reload
```

### 6. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

## API 接口

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 商品
- `GET /api/products` - 商品列表（分页、搜索）
- `GET /api/products/{id}` - 商品详情
- `POST /api/products` - 创建商品
- `PUT /api/products/{id}` - 更新商品
- `DELETE /api/products/{id}` - 删除商品（软删除）

### 购物车
- `GET /api/cart` - 获取购物车
- `POST /api/cart` - 添加到购物车
- `PUT /api/cart/{product_id}` - 更新数量
- `DELETE /api/cart/{product_id}` - 删除商品
- `DELETE /api/cart` - 清空购物车

### 订单
- `POST /api/orders` - 创建订单
- `GET /api/orders` - 我的订单列表
- `GET /api/orders/{id}` - 订单详情
- `PUT /api/orders/{id}/cancel` - 取消订单
- `PUT /api/orders/{id}/pay` - 支付订单（模拟）
- `PUT /api/orders/{id}/confirm` - 确认收货

### 后台管理（需要管理员权限）
- `GET /api/admin/users` - 用户列表
- `PUT /api/admin/users/{id}/status` - 禁用/启用用户
- `GET /api/admin/orders` - 所有订单
- `PUT /api/admin/orders/{id}/ship` - 发货
- `PUT /api/admin/orders/{id}/refund` - 退款
- `GET /api/admin/stats/sales` - 销售统计
- `GET /api/admin/stats/users` - 用户统计

### AI 智能客服（需要 OPENAI_API_KEY）
- `POST /api/ai/chat` - 智能客服问答（RAG）
- `POST /api/ai/search` - 语义搜索
- `GET /api/ai/recommend/{product_id}` - 商品推荐
- `GET /api/ai/status` - AI 服务状态

## 项目结构

```
ecommerce-api/
├── main.py                 # FastAPI 入口
├── config.py               # 配置
├── database.py             # 数据库连接
├── dependencies.py         # 依赖注入
├── models/                 # SQLAlchemy 模型
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   └── cart.py
├── schemas/                # Pydantic 模型
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   └── cart.py
├── routers/                # 路由
│   ├── auth.py
│   ├── products.py
│   ├── cart.py
│   ├── orders.py
│   ├── admin.py
│   └── ai.py               # AI 智能客服
└── services/               # 业务逻辑
    ├── auth_service.py
    ├── product_service.py
    ├── cart_service.py
    ├── order_service.py
    └── ai_service.py        # AI 服务（RAG、语义搜索、推荐）
```

## 设计要点

1. **数据快照**：订单项存储商品快照，历史不随当前改变
2. **状态机**：订单状态用转移表集中管理
3. **防超卖**：WHERE 条件扣减库存
4. **签名验证**：支付回调验签防止伪造
5. **幂等性**：重复回调只处理一次
6. **RAG 智能客服**：基于商品数据的检索增强生成，减少幻觉
7. **语义搜索**：理解用户意图，不只是关键词匹配
8. **降级策略**：AI 不可用时自动回退到关键词搜索
