"""
订单路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from services import order_service

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("", response_model=OrderResponse, summary="创建订单")
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建订单

    从购物车选中的商品创建订单，流程：
    1. 校验库存
    2. 扣减库存
    3. 创建订单 + 订单项（数据快照）
    4. 清除购物车
    """
    try:
        order = order_service.create_order(
            db, current_user.id, data.address, data.cart_item_ids, data.remark
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", summary="我的订单列表")
async def list_orders(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: str | None = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的订单列表"""
    return order_service.get_user_orders(db, current_user.id, page, size, status_filter)


@router.get("/{order_id}", response_model=OrderResponse, summary="订单详情")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取订单详情"""
    order = order_service.get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.put("/{order_id}/cancel", response_model=OrderResponse, summary="取消订单")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取消订单（仅 pending 状态可取消）

    取消后库存自动回滚
    """
    try:
        order = order_service.update_order_status(db, order_id, "cancelled", current_user.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{order_id}/pay", response_model=OrderResponse, summary="支付订单")
async def pay_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    模拟支付订单

    将订单状态从 pending 更新为 paid
    """
    try:
        order = order_service.update_order_status(db, order_id, "paid", current_user.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{order_id}/confirm", response_model=OrderResponse, summary="确认收货")
async def confirm_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    确认收货（仅 shipped 状态可确认）

    将订单状态从 shipped 更新为 completed
    """
    try:
        order = order_service.update_order_status(db, order_id, "completed", current_user.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
