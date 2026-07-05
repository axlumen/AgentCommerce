"""
商品路由：CRUD、分页、搜索
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.product import ProductCreate, ProductUpdate, ProductResponse, CategoryCreate, CategoryResponse
from services import product_service

router = APIRouter(prefix="/products", tags=["商品"])


@router.get("", summary="商品列表")
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    category_id: int | None = Query(None, description="分类 ID"),
    keyword: str | None = Query(None, description="搜索关键词"),
    is_on_sale: bool | None = Query(True, description="是否上架"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方式"),
    db: Session = Depends(get_db),
):
    """
    获取商品列表

    支持：分页、分类筛选、关键词搜索、排序
    """
    return product_service.get_products(db, page, size, category_id, keyword, is_on_sale, sort_by, sort_order)


@router.get("/{product_id}", response_model=ProductResponse, summary="商品详情")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """获取商品详情"""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return product


@router.post("", response_model=ProductResponse, summary="创建商品")
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    创建商品（需要登录）

    任何登录用户都可以创建商品（简化处理）
    """
    return product_service.create_product(db, data)


@router.put("/{product_id}", response_model=ProductResponse, summary="更新商品")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新商品（需要登录）"""
    product = product_service.update_product(db, product_id, data)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return product


@router.delete("/{product_id}", summary="删除商品")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除商品（软删除：下架）"""
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return {"message": "商品已下架"}


# 分类相关
@router.get("/categories/all", response_model=list[CategoryResponse], summary="分类列表")
async def list_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return product_service.get_categories(db)


@router.post("/categories", response_model=CategoryResponse, summary="创建分类")
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建分类（需要登录）"""
    return product_service.create_category(db, data.name, data.parent_id, data.sort_order)
