"""
商品服务：CRUD、分页、搜索
"""

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.product import Category, Product
from schemas.product import ProductCreate, ProductUpdate

# 排序字段白名单，防止注入
ALLOWED_SORT_FIELDS = {"created_at", "price", "sales_count", "name", "stock"}


def get_products(
    db: Session,
    page: int = 1,
    size: int = 10,
    category_id: int | None = None,
    keyword: str | None = None,
    is_on_sale: bool | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    """
    获取商品列表（分页、筛选、排序）
    """
    query = db.query(Product)

    # 分类筛选
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Product.name.contains(keyword),
                Product.description.contains(keyword),
            )
        )

    # 上架状态
    if is_on_sale is not None:
        query = query.filter(Product.is_on_sale == is_on_sale)

    # 总数
    total = query.count()

    # 排序（白名单校验）
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = "created_at"
    sort_column = getattr(Product, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 分页
    items = query.offset((page - 1) * size).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def get_product(db: Session, product_id: int) -> Product | None:
    """获取商品详情"""
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, data: ProductCreate) -> Product:
    """创建商品"""
    product = Product(**data.model_dump(), created_at=datetime.now())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product | None:
    """更新商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """删除商品（软删除：下架）"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return False

    product.is_on_sale = False
    db.commit()
    return True


# 分类相关
def get_categories(db: Session) -> list[Category]:
    """获取所有分类"""
    return db.query(Category).order_by(Category.sort_order).all()


def create_category(db: Session, name: str, parent_id: int | None = None, sort_order: int = 0) -> Category:
    """创建分类"""
    level = 1
    if parent_id:
        parent = db.query(Category).filter(Category.id == parent_id).first()
        if parent:
            level = parent.level + 1

    category = Category(name=name, parent_id=parent_id, level=level, sort_order=sort_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
