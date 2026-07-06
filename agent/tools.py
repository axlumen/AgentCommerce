"""
Agent 业务工具

6 个核心工具，使用上下文变量传递数据库会话。
"""

import contextvars
import json
import logging
import time
from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from agent.security import (
    detect_injection,
    sanitize_input,
)
from models.product import Product

logger = logging.getLogger(__name__)

# 请求级别的数据库会话（由 router 设置，工具执行时读取）
_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar(
    "agent_db_session", default=None
)
_user_id_context: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "agent_user_id", default=None
)


def set_request_context(db: Session, user_id: int | None = None) -> contextvars.Token:
    """设置请求上下文（router 调用）"""
    db_token = _db_context.set(db)
    if user_id is not None:
        _user_id_context.set(user_id)
    return db_token


def reset_request_context(db_token: contextvars.Token) -> None:
    """重置请求上下文"""
    _db_context.reset(db_token)


# ============================================================
# 工具调用记录（request-scoped，线程安全）
# ============================================================

_tool_call_log: contextvars.ContextVar[list[dict]] = contextvars.ContextVar(
    "tool_call_log", default=[]
)


def get_tool_call_log() -> list[dict]:
    """获取当前请求的工具调用记录"""
    return list(_tool_call_log.get())


def clear_tool_call_log() -> None:
    """清空工具调用记录（新请求开始时调用）"""
    _tool_call_log.set([])


def _record(tool_name: str, args: dict, result: Any, duration_ms: float) -> None:
    """记录工具调用"""
    log = _tool_call_log.get()
    log.append({
        "tool": tool_name,
        "args": args,
        "result": json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result,
        "timestamp": time.time(),
        "duration_ms": round(duration_ms, 2),
    })


# ============================================================
# 6 个核心业务工具
# ============================================================


@tool
def search_products(
    query: str,
    price_min: float | None = None,
    price_max: float | None = None,
    category_id: int | None = None,
) -> str:
    """
    搜索商品。支持关键词、价格区间、分类筛选。

    Args:
        query: 搜索关键词（如 "手机"、"耳机"）
        price_min: 最低价格（可选）
        price_max: 最高价格（可选）
        category_id: 分类 ID（可选）
    """
    start_time = time.time()

    if detect_injection(query):
        return json.dumps({"error": "输入包含不安全内容，请重新描述您的需求"}, ensure_ascii=False)

    query = sanitize_input(query, max_length=200)
    db = _db_context.get()

    try:
        # 优先使用三级混合检索
        try:
            from rag.retriever import get_retriever, fallback_search

            retriever = get_retriever()
            status = retriever.get_status()

            if status["mode"] != "fallback":
                # 构建过滤条件
                filters = {}
                if category_id is not None:
                    filters["category_id"] = category_id
                if price_min is not None:
                    filters["price_min"] = price_min
                if price_max is not None:
                    filters["price_max"] = price_max

                results = retriever.search(query, top_k=5, filters=filters)

                # 补充商品详情
                items = []
                for r in results:
                    product = db.query(Product).filter(Product.id == r.product_id).first()
                    if product:
                        items.append({
                            "id": product.id,
                            "name": product.name,
                            "price": float(product.price),
                            "stock": product.stock,
                            "category_id": product.category_id,
                            "brand": product.brand,
                            "sales_count": product.sales_count,
                            "relevance_score": round(r.score, 4),
                        })

                output = {"total": len(items), "items": items, "retrieval_mode": status["mode"]}
                _record("search_products", {"query": query}, output, (time.time() - start_time) * 1000)
                return json.dumps(output, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Hybrid retrieval failed, falling back: {e}")

        # 降级：MySQL LIKE 查询
        from services.product_service import get_products
        result = get_products(db, page=1, size=5, keyword=query, is_on_sale=True)

        items = []
        for p in result["items"]:
            if price_min is not None and float(p.price) < price_min:
                continue
            if price_max is not None and float(p.price) > price_max:
                continue
            if category_id is not None and p.category_id != category_id:
                continue
            items.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "stock": p.stock,
                "category_id": p.category_id,
                "sales_count": p.sales_count,
            })

        output = {"total": len(items), "items": items, "retrieval_mode": "mysql_fallback"}
        _record("search_products", {"query": query}, output, (time.time() - start_time) * 1000)
        return json.dumps(output, ensure_ascii=False)

    except Exception as e:
        logger.exception("search_products failed")
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


@tool
def get_product_detail(product_id: int) -> str:
    """
    获取商品详情，包含库存、价格、规格信息。

    Args:
        product_id: 商品 ID
    """
    start_time = time.time()
    db = _db_context.get()

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)

        detail = {
            "id": product.id,
            "name": product.name,
            "description": product.description or "暂无描述",
            "price": float(product.price),
            "original_price": float(product.original_price) if product.original_price else None,
            "stock": product.stock,
            "category_id": product.category_id,
            "image_url": product.image_url,
            "is_on_sale": product.is_on_sale,
            "sales_count": product.sales_count,
        }
        if product.original_price and product.original_price > product.price:
            detail["discount"] = round(float(product.price) / float(product.original_price) * 100, 1)

        _record("get_product_detail", {"product_id": product_id}, detail, (time.time() - start_time) * 1000)
        return json.dumps(detail, ensure_ascii=False)

    except Exception as e:
        logger.exception("get_product_detail failed")
        return json.dumps({"error": f"获取商品详情失败: {str(e)}"}, ensure_ascii=False)


@tool
def check_stock(product_id: int, quantity: int = 1) -> str:
    """
    校验商品库存是否充足。

    Args:
        product_id: 商品 ID
        quantity: 需要的数量
    """
    start_time = time.time()
    db = _db_context.get()

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)

        result = {
            "product_id": product_id,
            "product_name": product.name,
            "requested_quantity": quantity,
            "available_stock": product.stock,
            "sufficient": product.stock >= quantity,
            "message": f"库存充足，当前有 {product.stock} 件" if product.stock >= quantity else f"库存不足，当前仅剩 {product.stock} 件",
        }

        _record("check_stock", {"product_id": product_id, "quantity": quantity}, result, (time.time() - start_time) * 1000)
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.exception("check_stock failed")
        return json.dumps({"error": f"库存校验失败: {str(e)}"}, ensure_ascii=False)


@tool
def calculate_final_price(
    product_id: int,
    quantity: int = 1,
    coupon_code: str | None = None,
) -> str:
    """
    计算商品最终价格（含优惠计算）。

    Args:
        product_id: 商品 ID
        quantity: 数量
        coupon_code: 优惠券代码（可选）
    """
    start_time = time.time()
    db = _db_context.get()

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)

        unit_price = float(product.price)
        original_unit_price = float(product.original_price) if product.original_price else unit_price
        subtotal = unit_price * quantity
        original_subtotal = original_unit_price * quantity
        discount_amount = original_subtotal - subtotal

        result = {
            "product_id": product_id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": unit_price,
            "original_unit_price": original_unit_price,
            "subtotal": round(subtotal, 2),
            "original_subtotal": round(original_subtotal, 2),
            "discount_amount": round(discount_amount, 2),
            "coupon_applied": False,
        }
        if coupon_code:
            result["coupon_code"] = coupon_code
            result["coupon_message"] = "优惠券功能暂未开放"

        _record("calculate_final_price", {"product_id": product_id, "quantity": quantity}, result, (time.time() - start_time) * 1000)
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.exception("calculate_final_price failed")
        return json.dumps({"error": f"价格计算失败: {str(e)}"}, ensure_ascii=False)


@tool
def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """
    将商品加入购物车。这是一个敏感操作，需要用户确认。

    Args:
        product_id: 商品 ID
        quantity: 数量（1-99）
    """
    start_time = time.time()
    db = _db_context.get()
    user_id = _user_id_context.get()

    if not user_id:
        return json.dumps({"error": "请先登录"}, ensure_ascii=False)

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)
        if not product.is_on_sale:
            return json.dumps({"error": f"商品 {product.name} 已下架"}, ensure_ascii=False)
        if product.stock < quantity:
            return json.dumps({"error": f"库存不足，{product.name} 仅剩 {product.stock} 件"}, ensure_ascii=False)

        from services.cart_service import add_to_cart as cart_add
        cart_add(user_id, product_id, quantity)

        result = {
            "success": True,
            "product_id": product_id,
            "product_name": product.name,
            "quantity": quantity,
            "message": f"已将 {product.name} x{quantity} 加入购物车",
        }

        _record("add_to_cart", {"product_id": product_id, "quantity": quantity}, result, (time.time() - start_time) * 1000)
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.exception("add_to_cart failed")
        return json.dumps({"error": f"加购失败: {str(e)}"}, ensure_ascii=False)


@tool
def get_user_preferences() -> str:
    """获取用户偏好和历史购买记录，用于个性化推荐。"""
    start_time = time.time()
    user_id = _user_id_context.get()

    if not user_id:
        return json.dumps({"preferences": {}, "message": "未登录，无法获取偏好"}, ensure_ascii=False)

    try:
        from agent.memory import memory_manager
        prefs = memory_manager.get_user_preferences(user_id)

        if not prefs:
            # 尝试从对话历史中提取（简化版，不访问 messages）
            prefs = {}

        result = {"user_id": user_id, "preferences": prefs}
        _record("get_user_preferences", {}, result, (time.time() - start_time) * 1000)
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.exception("get_user_preferences failed")
        return json.dumps({"error": f"获取偏好失败: {str(e)}"}, ensure_ascii=False)


@tool
def compare_products(product_ids: str) -> str:
    """
    比较多个商品的价格、库存、规格。用于用户想对比不同商品时。

    Args:
        product_ids: 商品 ID 列表，逗号分隔（如 "1,2,3"）
    """
    start_time = time.time()
    db = _db_context.get()

    try:
        # 解析 ID 列表
        ids = [int(id.strip()) for id in product_ids.split(",") if id.strip()]
        if not ids or len(ids) < 2:
            return json.dumps({"error": "请至少提供 2 个商品 ID"}, ensure_ascii=False)
        if len(ids) > 5:
            return json.dumps({"error": "最多比较 5 个商品"}, ensure_ascii=False)

        # 查询商品
        products = db.query(Product).filter(Product.id.in_(ids)).all()
        if not products:
            return json.dumps({"error": "未找到商品"}, ensure_ascii=False)

        # 构建对比数据
        items = []
        for p in products:
            item = {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "original_price": float(p.original_price) if p.original_price else None,
                "stock": p.stock,
                "brand": p.brand or "未知",
                "sales_count": p.sales_count,
                "is_on_sale": p.is_on_sale,
            }
            # 计算折扣
            if p.original_price and p.original_price > p.price:
                item["discount"] = round(float(p.price) / float(p.original_price) * 100, 1)
            items.append(item)

        # 按价格排序
        items.sort(key=lambda x: x["price"])

        # 找出最优项
        cheapest = items[0]
        most_stock = max(items, key=lambda x: x["stock"])
        most_sales = max(items, key=lambda x: x["sales_count"])

        result = {
            "total": len(items),
            "items": items,
            "summary": {
                "cheapest": {"id": cheapest["id"], "name": cheapest["name"], "price": cheapest["price"]},
                "most_stock": {"id": most_stock["id"], "name": most_stock["name"], "stock": most_stock["stock"]},
                "most_popular": {"id": most_sales["id"], "name": most_sales["name"], "sales": most_sales["sales_count"]},
            }
        }

        _record("compare_products", {"product_ids": product_ids}, result, (time.time() - start_time) * 1000)
        return json.dumps(result, ensure_ascii=False)

    except ValueError:
        return json.dumps({"error": "商品 ID 必须是数字"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("compare_products failed")
        return json.dumps({"error": f"比较失败: {str(e)}"}, ensure_ascii=False)


# 工具列表（供 graph.py 使用）
TOOL_LIST = [
    search_products,
    get_product_detail,
    check_stock,
    calculate_final_price,
    add_to_cart,
    get_user_preferences,
    compare_products,
]

TOOLS_BY_NAME = {t.name: t for t in TOOL_LIST}
