"""
购物车服务：Redis Hash 实现
"""

import json

from sqlalchemy.orm import Session

from config import CART_KEY_PREFIX, CART_EXPIRE_DAYS
from models.product import Product
from redis_client import get_redis
from services.exceptions import NotFoundError, ConflictError


def get_cart_key(user_id: int) -> str:
    """生成购物车 key"""
    return f"{CART_KEY_PREFIX}{user_id}"


def add_to_cart(user_id: int, product_id: int, quantity: int, db: Session) -> bool:
    """
    添加商品到购物车（含业务校验）

    使用 Redis Hash:
    - key: cart:{user_id}
    - field: product:{product_id}
    - value: quantity
    """
    if not get_redis():
        raise ValueError("Redis 不可用")

    # 业务校验：商品存在性、上架状态、库存
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("商品不存在")
    if not product.is_on_sale:
        raise ConflictError("商品已下架")
    if quantity > product.stock:
        raise ConflictError("库存不足")

    cart_key = get_cart_key(user_id)
    field = f"product:{product_id}"

    # 检查商品是否已在购物车
    existing = get_redis().hget(cart_key, field)
    if existing:
        new_quantity = int(existing) + quantity
        get_redis().hset(cart_key, field, new_quantity)
    else:
        get_redis().hset(cart_key, field, quantity)

    # 设置过期时间
    get_redis().expire(cart_key, CART_EXPIRE_DAYS * 24 * 3600)
    return True


def update_cart_item(user_id: int, product_id: int, quantity: int) -> bool:
    """
    更新购物车商品数量

    quantity=0 表示删除
    """
    if not get_redis():
        raise ValueError("Redis 不可用")

    cart_key = get_cart_key(user_id)
    field = f"product:{product_id}"

    if quantity == 0:
        get_redis().hdel(cart_key, field)
    else:
        get_redis().hset(cart_key, field, quantity)

    return True


def remove_from_cart(user_id: int, product_id: int) -> bool:
    """从购物车删除商品"""
    if not get_redis():
        raise ValueError("Redis 不可用")

    cart_key = get_cart_key(user_id)
    field = f"product:{product_id}"
    get_redis().hdel(cart_key, field)
    return True


def _parse_cart_data(cart_data: dict) -> list[tuple[int, int]]:
    """解析 Redis Hash 购物车数据为 (product_id, quantity) 列表"""
    parsed = []
    for field, quantity_str in cart_data.items():
        product_id = int(field.split(":")[1])
        quantity = int(quantity_str)
        parsed.append((product_id, quantity))
    return parsed


def _batch_query_products(db: Session, product_ids: list[int]) -> dict[int, Product]:
    """批量查询商品，返回 {product_id: Product} 映射"""
    if not product_ids:
        return {}
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    return {p.id: p for p in products}


def get_cart(user_id: int, db: Session) -> dict:
    """
    获取购物车详情

    返回:
        {
            "items": [...],
            "total_amount": float,
            "selected_count": int
        }
    """
    if not get_redis():
        return {"items": [], "total_amount": 0.0, "selected_count": 0}

    cart_key = get_cart_key(user_id)
    cart_data = get_redis().hgetall(cart_key)

    if not cart_data:
        return {"items": [], "total_amount": 0.0, "selected_count": 0}

    cart_items = _parse_cart_data(cart_data)
    product_ids = [pid for pid, _ in cart_items]
    product_map = _batch_query_products(db, product_ids)

    items = []
    total_amount = 0.0

    for product_id, quantity in cart_items:
        product = product_map.get(product_id)
        if not product:
            continue

        subtotal = float(product.price) * quantity
        items.append({
            "product_id": product.id,
            "product_name": product.name,
            "product_price": float(product.price),
            "product_image": product.image_url,
            "quantity": quantity,
            "subtotal": subtotal,
            "stock": product.stock,
        })
        total_amount += subtotal

    return {
        "items": items,
        "total_amount": round(total_amount, 2),
        "selected_count": len(items),
    }


def clear_cart(user_id: int) -> bool:
    """清空购物车"""
    if not get_redis():
        return False

    cart_key = get_cart_key(user_id)
    get_redis().delete(cart_key)
    return True


def get_selected_items(user_id: int, cart_item_ids: list[int], db: Session) -> list[dict]:
    """
    获取选中的购物车项

    返回:
        [{"product_id": int, "quantity": int, "product": Product}, ...]
    """
    if not get_redis():
        return []

    cart_key = get_cart_key(user_id)

    # 批量获取选中项的数量
    pipe = get_redis().pipeline()
    for product_id in cart_item_ids:
        pipe.hget(cart_key, f"product:{product_id}")
    quantity_strs = pipe.execute()

    # 收集有效 product_id
    valid_ids = []
    quantity_map = {}
    for product_id, quantity_str in zip(cart_item_ids, quantity_strs):
        if quantity_str:
            valid_ids.append(product_id)
            quantity_map[product_id] = int(quantity_str)

    # 批量查询商品
    product_map = _batch_query_products(db, valid_ids)

    items = []
    for product_id in valid_ids:
        product = product_map.get(product_id)
        if not product:
            continue
        items.append({
            "product_id": product.id,
            "quantity": quantity_map[product_id],
            "product": product,
        })

    return items
