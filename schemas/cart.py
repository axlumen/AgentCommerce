"""
购物车相关 Pydantic 模型
"""

from pydantic import BaseModel, Field


class CartAddRequest(BaseModel):
    """添加购物车"""
    product_id: int = Field(..., description="商品 ID")
    quantity: int = Field(1, ge=1, description="数量")


class CartUpdateRequest(BaseModel):
    """更新购物车"""
    quantity: int = Field(..., ge=0, description="数量（0 表示删除）")


class CartItemResponse(BaseModel):
    """购物车项响应"""
    product_id: int
    product_name: str
    product_price: float
    product_image: str | None
    quantity: int
    subtotal: float
    stock: int  # 商品库存，用于前端判断


class CartResponse(BaseModel):
    """购物车响应"""
    items: list[CartItemResponse]
    total_amount: float
    selected_count: int
