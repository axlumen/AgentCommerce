"""
商品模型
"""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, DECIMAL, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)

    # 关联
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2))
    stock = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(500))
    brand = Column(String(100), nullable=True, index=True)
    specs = Column(JSON, nullable=True)
    is_on_sale = Column(Boolean, default=True)
    sales_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    category = relationship("Category", back_populates="products")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_product_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_product_price_non_negative"),
    )
