"""
商品相关 Pydantic 模型
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """创建分类"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    parent_id: int | None = Field(None, description="父分类 ID")
    sort_order: int = Field(0, description="排序序号")


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    parent_id: int | None
    level: int
    sort_order: int

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    """创建商品"""
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    description: str | None = Field(None, description="商品描述")
    price: float = Field(..., gt=0, description="价格")
    original_price: float | None = Field(None, description="原价")
    stock: int = Field(..., ge=0, description="库存")
    category_id: int | None = Field(None, description="分类 ID")
    image_url: str | None = Field(None, description="商品图片")
    brand: str | None = Field(None, max_length=100, description="品牌")
    specs: dict | None = Field(None, description="规格参数")


class ProductUpdate(BaseModel):
    """更新商品"""
    name: str | None = Field(None, min_length=1, max_length=200, description="商品名称")
    description: str | None = Field(None, description="商品描述")
    price: float | None = Field(None, gt=0, description="价格")
    original_price: float | None = Field(None, description="原价")
    stock: int | None = Field(None, ge=0, description="库存")
    category_id: int | None = Field(None, description="分类 ID")
    image_url: str | None = Field(None, description="商品图片")
    brand: str | None = Field(None, max_length=100, description="品牌")
    specs: dict | None = Field(None, description="规格参数")
    is_on_sale: bool | None = Field(None, description="是否上架")


class ProductResponse(BaseModel):
    """商品响应"""
    id: int
    name: str
    description: str | None
    price: Decimal
    original_price: Decimal | None
    stock: int
    category_id: int | None
    image_url: str | None
    brand: str | None
    specs: dict | None
    is_on_sale: bool
    sales_count: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
