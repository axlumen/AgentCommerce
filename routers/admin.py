"""
后台管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_admin
from models.order import Order
from models.product import Product
from models.user import User
from schemas.order import OrderResponse
from services import order_service, product_service
from services.exceptions import BusinessError

router = APIRouter(prefix="/admin", tags=["后台管理"], dependencies=[Depends(get_current_admin)])


@router.post("/invalidate-cache", summary="清除语义缓存")
async def invalidate_cache():
    """清除语义缓存（管理员用）"""
    from cache.semantic_cache import semantic_cache
    semantic_cache.invalidate_all()
    return {"message": "Cache invalidated"}


# ==================== 用户管理 ====================

@router.get("/users", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """管理员查看用户列表"""
    query = db.query(User)
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.put("/users/{user_id}/status", summary="禁用/启用用户")
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
):
    """禁用或启用用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = is_active
    db.commit()
    return {"message": f"用户已{'启用' if is_active else '禁用'}"}


# ==================== 订单管理 ====================

@router.get("/orders", summary="所有订单")
async def list_all_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """管理员查看所有订单"""
    return order_service.get_orders(db, page=page, size=size, status=status_filter)


@router.put("/orders/{order_id}/ship", response_model=OrderResponse, summary="发货")
async def ship_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    """
    订单发货（仅 paid 状态可发货）

    将订单状态从 paid 更新为 shipped
    """
    try:
        order = order_service.update_order_status(db, order_id, "shipped")
        return order
    except BusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.put("/orders/{order_id}/refund", response_model=OrderResponse, summary="退款")
async def refund_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    """
    订单退款

    将订单状态更新为 refunded，库存自动回滚
    """
    try:
        order = order_service.update_order_status(db, order_id, "refunded")
        return order
    except BusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


# ==================== 数据统计 ====================

@router.get("/stats/sales", summary="销售统计")
async def get_sales_stats(
    db: Session = Depends(get_db),
):
    """销售统计"""
    # 总销售额
    total_sales = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_(["paid", "shipped", "completed"])
    ).scalar() or 0

    # 总订单数
    total_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_(["paid", "shipped", "completed"])
    ).scalar() or 0

    # 各状态订单数
    status_counts = {}
    for s in ["pending", "paid", "shipped", "completed", "cancelled", "refunded"]:
        count = db.query(func.count(Order.id)).filter(Order.status == s).scalar() or 0
        status_counts[s] = count

    # 商品销量排行
    top_products = db.query(
        Product.name, Product.sales_count
    ).order_by(Product.sales_count.desc()).limit(10).all()

    return {
        "total_sales": float(total_sales),
        "total_orders": total_orders,
        "status_counts": status_counts,
        "top_products": [{"name": p.name, "sales_count": p.sales_count} for p in top_products],
    }


@router.get("/stats/users", summary="用户统计")
async def get_user_stats(
    db: Session = Depends(get_db),
):
    """用户统计"""
    from datetime import datetime, timedelta

    # 总用户数
    total_users = db.query(func.count(User.id)).scalar() or 0

    # 今日新增
    today = datetime.now().date()
    new_today = db.query(func.count(User.id)).filter(
        func.date(User.created_at) == today
    ).scalar() or 0

    # 活跃用户（近 30 天有订单）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_users = db.query(func.count(func.distinct(Order.user_id))).filter(
        Order.created_at >= thirty_days_ago
    ).scalar() or 0

    return {
        "total_users": total_users,
        "new_today": new_today,
        "active_users": active_users,
    }
