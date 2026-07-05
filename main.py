"""
电商 API 主入口

启动方式：
    uvicorn main:app --reload

API 文档：
    http://localhost:8000/docs

前端页面：
    http://localhost:8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import create_tables
from routers import auth, products, cart, orders, admin, ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时创建表"""
    create_tables()
    yield


app = FastAPI(
    title="电商 API",
    description="一个完整的电商后端 API，包含用户认证、商品管理、购物车、订单、支付、后台管理等模块。",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
frontend_dir = Path(__file__).parent / "frontend"

# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(frontend_dir / "index.html")


@app.get("/style.css")
async def css():
    """返回 CSS"""
    return FileResponse(frontend_dir / "style.css", media_type="text/css")


@app.get("/app.js")
async def js():
    """返回 JavaScript"""
    return FileResponse(frontend_dir / "app.js", media_type="application/javascript")


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.get("/api-info")
async def api_info():
    """API 信息"""
    return {
        "message": "电商 API",
        "docs": "/docs",
        "version": "1.0.0",
    }
