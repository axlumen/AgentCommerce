"""
Agent 安全控制模块

职责：
- 工具调用权限分级（read / write / admin）
- 输入清洗与 Prompt 注入防护
- 工具参数校验
"""

import re
import time

# ============================================================
# 工具权限分级
# ============================================================

TOOL_PERMISSIONS: dict[str, str] = {
    "search_products": "read",
    "get_product_detail": "read",
    "check_stock": "read",
    "calculate_final_price": "read",
    "add_to_cart": "write",
    "get_user_preferences": "read",
}

# 需要用户确认的工具
SENSITIVE_TOOLS: set[str] = {"add_to_cart"}


def check_tool_permission(tool_name: str, user_role: str = "user") -> bool:
    """
    检查工具调用权限

    Args:
        tool_name: 工具名称
        user_role: 用户角色（user / admin）

    Returns:
        是否允许调用
    """
    required_level = TOOL_PERMISSIONS.get(tool_name)
    if required_level is None:
        # 未知工具，默认拒绝
        return False

    if required_level == "read":
        return True
    if required_level == "write":
        return user_role in ("user", "admin")
    if required_level == "admin":
        return user_role == "admin"

    return False


def requires_confirmation(tool_name: str) -> bool:
    """检查工具是否需要用户确认"""
    return tool_name in SENSITIVE_TOOLS


# ============================================================
# Prompt 注入防护
# ============================================================

# 常见注入模式（不区分大小写）
INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", re.I),
    re.compile(r"forget\s+(everything|all|previous)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"override\s+(all|previous|system)", re.I),
    re.compile(r"disregard\s+(all|previous|above)", re.I),
    re.compile(r"act\s+as\s+(if|though)\s+you", re.I),
    re.compile(r"pretend\s+you\s+(are|have|can)", re.I),
    re.compile(r"\[INST\]|\[/INST]|<\|im_start\|>|<\|im_end\|>", re.I),
]


def detect_injection(text: str) -> bool:
    """
    检测输入中是否包含 Prompt 注入模式

    Args:
        text: 用户输入文本

    Returns:
        是否检测到注入尝试
    """
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    清洗用户输入

    Args:
        text: 原始输入
        max_length: 最大允许长度

    Returns:
        清洗后的文本
    """
    if not text:
        return ""

    # 截断超长输入
    if len(text) > max_length:
        text = text[:max_length]

    # 移除零宽字符
    text = re.sub(r"[​‌‍﻿]", "", text)

    # 移除控制字符（保留换行和制表符）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()


# ============================================================
# 参数校验
# ============================================================


def validate_tool_args(tool_name: str, args: dict) -> dict:
    """
    校验并清洗工具参数

    Args:
        tool_name: 工具名称
        args: 原始参数

    Returns:
        校验后的参数

    Raises:
        ValueError: 参数不合法
    """
    validated = {}

    if tool_name == "search_products":
        query = args.get("query", "")
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError("搜索词无效或过长")
        validated["query"] = sanitize_input(query, max_length=200)
        if "price_min" in args:
            validated["price_min"] = _validate_number(args["price_min"], "price_min", min_val=0)
        if "price_max" in args:
            validated["price_max"] = _validate_number(args["price_max"], "price_max", min_val=0)
        if "category_id" in args:
            validated["category_id"] = _validate_int(args["category_id"], "category_id", min_val=1)

    elif tool_name == "get_product_detail":
        validated["product_id"] = _validate_int(args.get("product_id"), "product_id", min_val=1)

    elif tool_name == "check_stock":
        validated["product_id"] = _validate_int(args.get("product_id"), "product_id", min_val=1)
        validated["quantity"] = _validate_int(args.get("quantity"), "quantity", min_val=1)

    elif tool_name == "calculate_final_price":
        validated["product_id"] = _validate_int(args.get("product_id"), "product_id", min_val=1)
        validated["quantity"] = _validate_int(args.get("quantity"), "quantity", min_val=1)
        if "coupon_code" in args and args["coupon_code"]:
            validated["coupon_code"] = sanitize_input(str(args["coupon_code"]), max_length=50)

    elif tool_name == "add_to_cart":
        validated["product_id"] = _validate_int(args.get("product_id"), "product_id", min_val=1)
        validated["quantity"] = _validate_int(args.get("quantity"), "quantity", min_val=1, max_val=99)

    elif tool_name == "get_user_preferences":
        pass  # 无需参数

    else:
        raise ValueError(f"未知工具: {tool_name}")

    return validated


def _validate_int(value, name: str, min_val: int | None = None, max_val: int | None = None) -> int:
    """校验整数参数"""
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"参数 {name} 必须是整数")

    if min_val is not None and val < min_val:
        raise ValueError(f"参数 {name} 不能小于 {min_val}")
    if max_val is not None and val > max_val:
        raise ValueError(f"参数 {name} 不能大于 {max_val}")

    return val


def _validate_number(value, name: str, min_val: float | None = None) -> float:
    """校验数值参数"""
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"参数 {name} 必须是数值")

    if min_val is not None and val < min_val:
        raise ValueError(f"参数 {name} 不能小于 {min_val}")

    return val
