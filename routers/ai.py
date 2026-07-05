"""
AI 智能客服路由

提供三个 AI 功能：
1. /api/ai/chat — 智能客服问答（RAG）
2. /api/ai/search — 语义搜索
3. /api/ai/recommend/{product_id} — 商品推荐
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.product import Product
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
    product_id: int | None = None  # 可选：指定商品 ID


class ChatResponse(BaseModel):
    """智能客服响应"""
    answer: str
    source: str = "ai"  # ai 或 fallback


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
    智能客服问答（RAG）

    用户提问，AI 基于商品数据回答。
    示例问题：
    - "iPhone 15 有几种颜色？"
    - "哪个手机性价比最高？"
    - "有什么适合送礼的商品？"
    """
    if not is_ai_available():
        raise HTTPException(status_code=503, detail="AI 服务不可用")

    # 检索相关商品
    if request.product_id:
        # 指定商品：查询该商品信息
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        products = [{
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description or ""
        }]
    else:
        # 未指定：查询所有商品（实际应做向量检索）
        all_products = db.query(Product).limit(20).all()
        products = [{
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "description": p.description or ""
        } for p in all_products]

    # RAG：基于商品数据生成回答
    answer = answer_product_question(request.question, products)

    return ChatResponse(answer=answer, source="ai")


@router.post("/search")
async def ai_search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    语义搜索

    理解用户意图，返回相关商品。
    示例：
    - "适合打游戏的手机" → 返回高性能手机
    - "送女朋友的礼物" → 返回热门商品
    """
    if not is_ai_available():
        # AI 不可用时，回退到数据库模糊搜索
        products = db.query(Product).filter(
            Product.name.contains(request.query) |
            Product.description.contains(request.query)
        ).limit(request.limit).all()
        return {"products": [{"id": p.id, "name": p.name, "price": p.price} for p in products]}

    # 获取所有商品
    all_products = db.query(Product).all()
    product_dicts = [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "description": p.description or ""
    } for p in all_products]

    # 语义搜索
    results = semantic_search(request.query, product_dicts)

    return {"products": results[:request.limit]}


@router.get("/recommend/{product_id}", response_model=RecommendResponse)
async def ai_recommend(product_id: int, limit: int = 3, db: Session = Depends(get_db)):
    """
    商品推荐

    基于当前商品推荐相似商品。
    示例：查看 iPhone 15 → 推荐 iPhone 15 Pro、AirPods、手机壳
    """
    # 获取当前商品
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 获取所有商品
    all_products = db.query(Product).filter(Product.id != product_id).all()
    product_dicts = [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "description": p.description or ""
    } for p in all_products]

    # 推荐
    if is_ai_available():
        recommended = recommend_products(product.name, product_dicts, limit)
    else:
        # AI 不可用时，返回同类别商品
        recommended = [p for p in product_dicts][:limit]

    return RecommendResponse(products=recommended)


@router.get("/status")
async def ai_status():
    """检查 AI 服务状态"""
    return {
        "available": is_ai_available(),
        "features": {
            "chat": is_ai_available(),
            "search": True,  # 搜索总是可用（有回退方案）
            "recommend": True,
        }
    }
