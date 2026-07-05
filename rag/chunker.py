"""
结构化分块器

将商品数据拆分为多个可索引的文本块，每个块携带元数据。
用于向量索引构建时的文本表示。
"""

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProductChunk:
    """商品文本块"""
    product_id: int
    chunk_type: str        # name, description, specs, full
    text: str              # 索引用文本
    metadata: dict = field(default_factory=dict)


def chunk_product(product: dict) -> list[ProductChunk]:
    """
    将单个商品拆分为多个文本块

    Args:
        product: 商品字典，需包含 id, name, description, price 等字段

    Returns:
        文本块列表
    """
    product_id = product["id"]
    name = product.get("name", "")
    description = product.get("description", "")
    price = product.get("price", 0)
    brand = product.get("brand", "")
    category_id = product.get("category_id")
    specs = product.get("specs") or {}

    # 基础元数据
    base_metadata = {
        "product_id": product_id,
        "category_id": category_id,
        "price": float(price),
        "brand": brand,
    }

    chunks = []

    # 块1：名称 + 摘要（用于快速匹配）
    short_text = name
    if description:
        # 取描述前 100 字符作为摘要
        short_desc = description[:100] + ("..." if len(description) > 100 else "")
        short_text = f"{name} - {short_desc}"
    chunks.append(ProductChunk(
        product_id=product_id,
        chunk_type="name",
        text=short_text,
        metadata={**base_metadata, "chunk_type": "name"},
    ))

    # 块2：详细描述（用于深度语义匹配）
    if description:
        chunks.append(ProductChunk(
            product_id=product_id,
            chunk_type="description",
            text=description,
            metadata={**base_metadata, "chunk_type": "description"},
        ))

    # 块3：规格参数（用于属性匹配）
    specs_parts = []
    if brand:
        specs_parts.append(f"品牌：{brand}")
    if specs:
        for key, value in specs.items():
            specs_parts.append(f"{key}：{value}")
    if specs_parts:
        specs_text = "，".join(specs_parts)
        chunks.append(ProductChunk(
            product_id=product_id,
            chunk_type="specs",
            text=specs_text,
            metadata={**base_metadata, "chunk_type": "specs"},
        ))

    # 块4：完整文本（用于嵌入生成）
    full_parts = [f"商品名称：{name}"]
    if description:
        full_parts.append(f"描述：{description}")
    if brand:
        full_parts.append(f"品牌：{brand}")
    if specs:
        specs_str = "，".join(f"{k}：{v}" for k, v in specs.items())
        full_parts.append(f"规格：{specs_str}")
    full_parts.append(f"价格：¥{price}")

    chunks.append(ProductChunk(
        product_id=product_id,
        chunk_type="full",
        text="\n".join(full_parts),
        metadata={**base_metadata, "chunk_type": "full"},
    ))

    return chunks


def chunk_products(products: list[dict]) -> list[ProductChunk]:
    """
    批量拆分商品为文本块

    Args:
        products: 商品字典列表

    Returns:
        所有文本块列表
    """
    all_chunks = []
    for product in products:
        try:
            chunks = chunk_product(product)
            all_chunks.extend(chunks)
        except Exception as e:
            logger.warning(f"Failed to chunk product {product.get('id')}: {e}")
    return all_chunks


def get_embeddable_text(product: dict) -> str:
    """
    获取用于嵌入的文本（单个商品的完整表示）

    简化版：直接返回完整文本，不拆分。
    适用于快速构建向量索引。
    """
    parts = [product.get("name", "")]
    desc = product.get("description", "")
    if desc:
        parts.append(desc[:200])
    brand = product.get("brand", "")
    if brand:
        parts.append(f"品牌：{brand}")
    specs = product.get("specs") or {}
    if specs:
        specs_str = "，".join(f"{k}：{v}" for k, v in specs.items())
        parts.append(specs_str)
    return " ".join(parts)
