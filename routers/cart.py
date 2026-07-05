"""
购物车路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.cart import CartAddRequest, CartUpdateRequest, CartResponse
from services import cart_service

router = APIRouter(prefix="/cart", tags=["购物车"])


@router.get("", response_model=CartResponse, summary="获取购物车")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的购物车"""
    if not cart_service.REDIS_AVAILABLE:
        return {"items": [], "total_amount": 0.0, "selected_count": 0}
    return cart_service.get_cart(current_user.id, db)


@router.post("", summary="添加到购物车")
async def add_to_cart(
    data: CartAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加商品到购物车"""
    # 检查 Redis 可用性
    if not cart_service.REDIS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="购物车服务不可用（Redis 未启动）"
        )

    # 检查商品是否存在
    from services.product_service import get_product
    product = get_product(db, data.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    if not product.is_on_sale:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="商品已下架")

    if data.quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")

    cart_service.add_to_cart(current_user.id, data.product_id, data.quantity)
    return {"message": "已添加到购物车"}


@router.put("/{product_id}", summary="更新购物车商品数量")
async def update_cart_item(
    product_id: int,
    data: CartUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """更新购物车商品数量（quantity=0 表示删除）"""
    cart_service.update_cart_item(current_user.id, product_id, data.quantity)
    return {"message": "购物车已更新"}


@router.delete("/{product_id}", summary="从购物车删除")
async def remove_from_cart(
    product_id: int,
    current_user: User = Depends(get_current_user),
):
    """从购物车删除商品"""
    cart_service.remove_from_cart(current_user.id, product_id)
    return {"message": "已从购物车删除"}


@router.delete("", summary="清空购物车")
async def clear_cart(
    current_user: User = Depends(get_current_user),
):
    """清空购物车"""
    cart_service.clear_cart(current_user.id)
    return {"message": "购物车已清空"}
