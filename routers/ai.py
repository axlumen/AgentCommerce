"""
AI 智能客服路由

提供三个 AI 功能：
1. /api/ai/chat — 智能客服问答（RAG + 语义缓存）
2. /api/ai/search — 语义搜索
3. /api/ai/recommend/{product_id} — 商品推荐

集成：语义缓存、限流、监控统计
"""

import logging
import time

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.product import Product
logger = logging.getLogger(__name__)

from services.ai_service import (
    is_ai_available,
    answer_product_question,
    semantic_search,
    recommend_products,
)

router = APIRouter(prefix="/ai", tags=["AI 智能客服"])


# ============================================================
# 请求/响应模型
# ============================================================

class ChatRequest(BaseModel):
    """智能客服请求"""
    question: str
    product_id: int | None = None


class ChatResponse(BaseModel):
    """智能客服响应"""
    answer: str
    source: str = "ai"
    cached: bool = False
    similarity: float | None = None


class SearchRequest(BaseModel):
    """语义搜索请求"""
    query: str
    limit: int = 5


class RecommendResponse(BaseModel):
    """商品推荐响应"""
    products: list[dict]


# ============================================================
# API 端点
# ============================================================

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    智能客服问答（RAG + 语义缓存）

    1. 先查语义缓存（相似度 ≥ 0.9 直接返回）
    2. 缓存未命中 → 混合检索 + LLM 生成
    3. 结果写入语义缓存
    """
    if not is_ai_available():
        raise HTTPException(status_code=503, detail="AI 服务不可用")

    # 检查语义缓存
    try:
        from cache.semantic_cache import semantic_cache
        from config import CACHE_SEMANTIC_ENABLED

        if CACHE_SEMANTIC_ENABLED and not request.product_id:
            cached = semantic_cache.get(request.question)
            if cached:
                return ChatResponse(
                    answer=cached["answer"],
                    source="cache",
                    cached=True,
                    similarity=cached["similarity"],
                )
    except Exception as e:
        logger.debug(f"Semantic cache get failed: {e}")

    # 检索相关商品
    if request.product_id:
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        products = [{
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description or "",
            "brand": product.brand or "",
        }]
    else:
        products = _hybrid_retrieve(request.question, db, top_k=5)

    answer = answer_product_question(request.question, products)

    # 写入语义缓存
    try:
        from cache.semantic_cache import semantic_cache
        from config import CACHE_SEMANTIC_ENABLED

        if CACHE_SEMANTIC_ENABLED and not request.product_id:
            product_ids = [p.get("id") for p in products if p.get("id")]
            semantic_cache.set(request.question, answer, product_ids)
    except Exception as e:
        logger.debug(f"Semantic cache set failed: {e}")

    return ChatResponse(answer=answer, source="ai", cached=False)


@router.post("/search")
async def ai_search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    语义搜索

    使用三级混合检索理解用户意图，返回相关商品。
    """
    products = _hybrid_retrieve(request.query, db, top_k=request.limit)

    if products:
        return {
            "products": [
                {"id": p["id"], "name": p["name"], "price": p["price"], "brand": p.get("brand")}
                for p in products
            ],
            "retrieval_mode": "hybrid",
        }

    # 降级
    products = db.query(Product).filter(
        Product.name.contains(request.query) |
        Product.description.contains(request.query)
    ).limit(request.limit).all()
    return {
        "products": [{"id": p.id, "name": p.name, "price": p.price} for p in products],
        "retrieval_mode": "mysql_fallback",
    }


@router.get("/recommend/{product_id}", response_model=RecommendResponse)
async def ai_recommend(product_id: int, limit: int = 3, db: Session = Depends(get_db)):
    """商品推荐"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    all_products = db.query(Product).filter(Product.id != product_id).all()
    product_dicts = [{
        "id": p.id, "name": p.name, "price": p.price, "description": p.description or ""
    } for p in all_products]

    if is_ai_available():
        recommended = recommend_products(product.name, product_dicts, limit)
    else:
        recommended = [p for p in product_dicts][:limit]

    return RecommendResponse(products=recommended)


@router.get("/status")
async def ai_status():
    """检查 AI 服务状态（含 RAG、缓存、熔断器状态）"""
    rag_status = {"available": False, "mode": "unknown"}
    try:
        from rag.retriever import get_retriever
        retriever = get_retriever()
        rag_status = retriever.get_status()
        rag_status["available"] = rag_status["mode"] != "fallback"
    except Exception as e:
        logger.debug(f"RAG status check failed: {e}")

    cache_status = {"available": False}
    try:
        from cache.semantic_cache import semantic_cache
        cache_status = semantic_cache.stats()
    except Exception as e:
        logger.debug(f"Cache status check failed: {e}")

    circuit_status = {}
    try:
        from monitoring.circuit_breaker import ai_circuit_breaker
        circuit_status = ai_circuit_breaker.get_info()
    except Exception as e:
        logger.debug(f"Circuit breaker status check failed: {e}")

    return {
        "available": is_ai_available(),
        "features": {
            "chat": is_ai_available(),
            "search": True,
            "recommend": True,
        },
        "rag": rag_status,
        "cache": cache_status,
        "circuit_breaker": circuit_status,
    }


@router.get("/stats")
async def ai_stats():
    """获取 AI 调用统计指标"""
    try:
        from monitoring.logger import get_stats
        return get_stats()
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# 辅助函数
# ============================================================


def _hybrid_retrieve(query: str, db: Session, top_k: int = 5) -> list[dict]:
    """混合检索商品（带降级）"""
    try:
        from rag.retriever import get_retriever, fallback_search

        retriever = get_retriever()
        status = retriever.get_status()

        if status["mode"] != "fallback":
            results = retriever.search(query, top_k=top_k)
            if results:
                product_ids = [r.product_id for r in results]
                products = db.query(Product).filter(Product.id.in_(product_ids)).all()
                product_map = {p.id: p for p in products}

                items = []
                for r in results:
                    p = product_map.get(r.product_id)
                    if p:
                        items.append({
                            "id": p.id,
                            "name": p.name,
                            "price": float(p.price),
                            "stock": p.stock,
                            "description": p.description or "",
                            "brand": p.brand or "",
                            "relevance_score": round(r.score, 4),
                        })
                return items

        return fallback_search(query, db_session=db, top_k=top_k)

    except Exception:
        from sqlalchemy import or_
        products = db.query(Product).filter(
            Product.is_on_sale == True,
            or_(
                Product.name.contains(query),
                Product.description.contains(query),
            )
        ).limit(top_k).all()
        return [
            {"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock, "description": p.description or ""}
            for p in products
        ]
