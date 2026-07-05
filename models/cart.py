"""
购物车模型（用于 Pydantic，实际存储在 Redis）
"""

from pydantic import BaseModel


class CartItem(BaseModel):
    """购物车项"""
    product_id: int
    quantity: int


class CartItemDetail(BaseModel):
    """购物车项详情（含商品信息）"""
    product_id: int
    product_name: str
    product_price: float
    product_image: str | None
    quantity: int
    subtotal: float
    selected: bool = True
