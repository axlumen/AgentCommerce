"""
订单模型
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    address_snapshot = Column(JSON, nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending/paid/shipped/completed/cancelled/refunded
    payment_method = Column(String(20))
    paid_at = Column(DateTime)
    shipped_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    remark = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    items = relationship("OrderItem", back_populates="order", lazy="joined")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)  # 快照
    product_price = Column(DECIMAL(10, 2), nullable=False)  # 快照
    product_image = Column(String(500))  # 快照
    quantity = Column(Integer, nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)

    # 关联
    order = relationship("Order", back_populates="items")


# 订单状态转移表
ORDER_STATUS_TRANSITIONS = {
    "pending": ["paid", "cancelled"],
    "paid": ["shipped", "refunded"],
    "shipped": ["completed", "refunded"],
    "completed": ["refunded"],
    "cancelled": [],
    "refunded": [],
}


def can_transition(current: str, target: str) -> bool:
    """检查状态流转是否合法"""
    return target in ORDER_STATUS_TRANSITIONS.get(current, [])
