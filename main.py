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

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import create_tables
from routers import auth, products, cart, orders, admin, ai, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时创建表、构建 RAG 索引"""
    create_tables()

    # 异步构建 RAG 索引（不阻塞启动）
    try:
        _build_rag_indexes()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"RAG index build skipped: {e}")

    yield


def _build_rag_indexes():
    """构建 RAG 检索索引"""
    import logging
    logger = logging.getLogger(__name__)

    from database import SessionLocal
    from models.product import Product

    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.is_on_sale == True).all()
        if not products:
            logger.info("No products found, skipping RAG index build")
            return

        product_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description or "",
                "price": float(p.price),
                "stock": p.stock,
                "category_id": p.category_id,
                "brand": p.brand or "",
                "specs": p.specs or {},
            }
            for p in products
        ]

        from rag.retriever import get_retriever
        retriever = get_retriever()
        retriever.build_index(product_dicts)
        logger.info(f"RAG indexes built for {len(product_dicts)} products")
    finally:
        db.close()


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

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求耗时和状态码"""
    start = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000

    # 只记录 API 请求（跳过静态文件）
    if request.url.path.startswith("/api"):
        logging.getLogger("request").info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed_ms:.0f}ms)"
        )
        response.headers["X-Response-Time"] = f"{elapsed_ms:.0f}ms"

    return response


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(agent.router, prefix="/api")


@app.post("/api/admin/invalidate-cache")
async def invalidate_cache():
    """清除语义缓存（管理员用）"""
    try:
        from cache.semantic_cache import semantic_cache
        semantic_cache.invalidate_all()
        return {"message": "Cache invalidated"}
    except Exception as e:
        return {"error": str(e)}


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
