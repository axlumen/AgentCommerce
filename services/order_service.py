"""
订单服务：创建订单、状态管理、库存扣减
"""

import random
import time
from datetime import datetime

from sqlalchemy.orm import Session

from models.order import Order, OrderItem, can_transition
from models.product import Product
from services.cart_service import clear_cart, get_selected_items, remove_from_cart
from services.exceptions import NotFoundError, ConflictError


def generate_order_no() -> str:
    """生成订单号：时间戳 + 随机数"""
    timestamp = int(time.time() * 1000)
    random_part = random.randint(1000, 9999)
    return f"{timestamp}{random_part}"


def create_order(db: Session, user_id: int, address: dict, cart_item_ids: list[int], remark: str | None = None) -> Order:
    """
    创建订单

    流程:
    1. 获取选中的购物车项
    2. 校验库存
    3. 扣减库存（WHERE 条件扣减）
    4. 创建订单 + 订单项（数据快照）
    5. 清除购物车

    异常:
        ValueError: 库存不足或商品不存在
    """
    # 步骤 1：获取选中的购物车项
    cart_items = get_selected_items(user_id, cart_item_ids, db)
    if not cart_items:
        raise NotFoundError("购物车为空")

    # 步骤 2-3：校验并扣减库存
    order_items_data = []
    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]

        # 检查是否上架
        if not product.is_on_sale:
            raise ConflictError(f"商品 {product.name} 已下架")

        # WHERE 条件扣减库存
        affected = db.query(Product).filter(
            Product.id == product.id,
            Product.stock >= quantity,
        ).update({"stock": Product.stock - quantity})

        if affected == 0:
            # 库存不足，回滚已扣减的库存
            for prev in order_items_data:
                db.query(Product).filter(Product.id == prev["product_id"]).update(
                    {"stock": Product.stock + prev["quantity"]}
                )
            db.commit()
            raise ConflictError(f"商品 {product.name} 库存不足")

        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "product_price": float(product.price),
            "product_image": product.image_url,
            "quantity": quantity,
            "subtotal": float(product.price) * quantity,
        })

    # 步骤 4：创建订单
    total_amount = sum(item["subtotal"] for item in order_items_data)

    order = Order(
        order_no=generate_order_no(),
        user_id=user_id,
        address_snapshot=address,
        total_amount=total_amount,
        remark=remark,
    )
    db.add(order)
    db.flush()  # 获取 order.id

    # 创建订单项
    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.add(order_item)

    # 步骤 5：先 commit DB，再清除购物车（避免 commit 失败导致购物车数据丢失）
    db.commit()
    db.refresh(order)

    for item in cart_items:
        remove_from_cart(user_id, item["product_id"])

    return order


def get_orders(db: Session, user_id: int | None = None, page: int = 1, size: int = 10, status: str | None = None) -> dict:
    """获取订单列表（user_id 为 None 时返回所有订单）"""
    query = db.query(Order)
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def get_order(db: Session, order_id: int, user_id: int | None = None) -> Order | None:
    """获取订单详情"""
    query = db.query(Order).filter(Order.id == order_id)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    return query.first()


def update_order_status(db: Session, order_id: int, target_status: str, user_id: int | None = None) -> Order:
    """
    更新订单状态

    异常:
        ValueError: 状态流转不合法
    """
    query = db.query(Order).filter(Order.id == order_id)
    if user_id:
        query = query.filter(Order.user_id == user_id)

    order = query.first()
    if not order:
        raise NotFoundError("订单不存在")

    if not can_transition(order.status, target_status):
        raise ConflictError(f"状态流转不合法: {order.status} -> {target_status}")

    # 更新状态和时间戳
    order.status = target_status
    now = datetime.now()

    if target_status == "paid":
        order.paid_at = now
    elif target_status == "shipped":
        order.shipped_at = now
    elif target_status == "completed":
        order.completed_at = now
    elif target_status == "cancelled":
        order.cancelled_at = now
        # 回滚库存
        for item in order.items:
            db.query(Product).filter(Product.id == item.product_id).update(
                {"stock": Product.stock + item.quantity}
            )

    db.commit()
    db.refresh(order)
    return order

