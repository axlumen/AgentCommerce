"""
订单相关 Pydantic 模型
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """创建订单"""
    address: dict = Field(..., description="收货地址")
    cart_item_ids: list[int] = Field(..., description="购物车项 ID 列表")
    remark: str | None = Field(None, max_length=500, description="订单备注")


class OrderItemResponse(BaseModel):
    """订单项响应"""
    id: int
    product_id: int
    product_name: str
    product_price: Decimal
    product_image: str | None
    quantity: int
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    user_id: int
    address_snapshot: dict
    total_amount: Decimal
    status: str
    payment_method: str | None
    paid_at: datetime | None
    shipped_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    remark: str | None
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    """更新订单状态"""
    status: str = Field(..., description="目标状态")
