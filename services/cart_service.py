"""
购物车服务：Redis Hash 实现
"""

import json

from sqlalchemy.orm import Session

from config import CART_KEY_PREFIX, CART_EXPIRE_DAYS
from models.product import Product
from redis_client import get_redis


def get_cart_key(user_id: int) -> str:
    """生成购物车 key"""
    return f"{CART_KEY_PREFIX}{user_id}"


def add_to_cart(user_id: int, product_id: int, quantity: int) -> bool:
    """
    添加商品到购物车

    使用 Redis Hash:
    - key: cart:{user_id}
    - field: product:{product_id}
    - value: quantity
    """
    if not get_redis():
        raise ValueError("Redis 不可用")

    cart_key = get_cart_key(user_id)
    field = f"product:{product_id}"

    # 检查商品是否已在购物车
    existing = get_redis().hget(cart_key, field)
    if existing:
        # 累加数量
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

    items = []
    total_amount = 0.0

    for field, quantity_str in cart_data.items():
        product_id = int(field.split(":")[1])
        quantity = int(quantity_str)

        # 查询商品信息
        product = db.query(Product).filter(Product.id == product_id).first()
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
    items = []

    for product_id in cart_item_ids:
        field = f"product:{product_id}"
        quantity_str = get_redis().hget(cart_key, field)
        if not quantity_str:
            continue

        quantity = int(quantity_str)
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            continue

        items.append({
            "product_id": product.id,
            "quantity": quantity,
            "product": product,
        })

    return items
