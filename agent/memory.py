"""
Agent 记忆系统

职责：
- 短期记忆：当前对话上下文（Redis 滑动窗口）
- 长期记忆：用户偏好提取与存储（Redis Hash）
- 状态追踪：多轮对话中记住用户需求
"""

import json
import logging
from datetime import datetime

from config import AGENT_CONTEXT_WINDOW, AGENT_SESSION_TTL
from redis_client import get_redis

logger = logging.getLogger(__name__)


class MemoryManager:
    """管理 Agent 的短期和长期记忆"""

    def __init__(self, max_short_term_messages: int = AGENT_CONTEXT_WINDOW):
        self.max_messages = max_short_term_messages

    @property
    def redis(self):
        return get_redis()

    # ============================================================
    # 短期记忆：对话上下文
    # ============================================================

    def _session_key(self, session_id: str) -> str:
        """生成会话存储 key"""
        return f"agent:session:{session_id}"

    def get_short_term(self, session_id: str) -> list[dict]:
        """
        获取短期记忆（当前对话上下文）

        Returns:
            消息列表 [{"role": str, "content": str}, ...]
        """
        if not self.redis:
            return []

        key = self._session_key(session_id)
        data = self.redis.get(key)
        if not data:
            return []

        try:
            messages = json.loads(data)
            return messages if isinstance(messages, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def save_short_term(self, session_id: str, messages: list[dict]) -> None:
        """
        保存短期记忆

        自动应用滑动窗口截断。
        """
        if not self.redis:
            return

        # 滑动窗口：只保留最近 N 条消息
        trimmed = self.trim_messages(messages)

        key = self._session_key(session_id)
        self.redis.setex(key, AGENT_SESSION_TTL, json.dumps(trimmed, ensure_ascii=False))

    def trim_messages(self, messages: list[dict]) -> list[dict]:
        """
        滑动窗口截断

        保留最近 max_messages 条消息，但确保第一条是 system 或 user 消息。
        """
        if len(messages) <= self.max_messages:
            return messages

        # 取末尾的 max_messages 条
        trimmed = messages[-self.max_messages :]

        # 确保第一条不是 assistant/tool 消息（否则 LLM 缺少上下文）
        while trimmed and trimmed[0].get("role") in ("assistant", "tool"):
            trimmed = trimmed[1:]

        return trimmed

    def clear_short_term(self, session_id: str) -> None:
        """清除会话的短期记忆"""
        if not self.redis:
            return

        key = self._session_key(session_id)
        self.redis.delete(key)

    # ============================================================
    # 长期记忆：用户偏好
    # ============================================================

    def _preferences_key(self, user_id: int) -> str:
        """生成用户偏好存储 key"""
        return f"agent:preferences:{user_id}"

    def get_user_preferences(self, user_id: int) -> dict:
        """
        获取用户长期偏好

        Returns:
            偏好字典，例如：
            {
                "preferred_categories": ["手机", "电脑"],
                "price_range": {"min": 1000, "max": 5000},
                "brands": ["Apple", "华为"],
                "last_updated": "2024-01-01T00:00:00"
            }
        """
        if not self.redis:
            return {}

        key = self._preferences_key(user_id)
        data = self.redis.get(key)
        if not data:
            return {}

        try:
            prefs = json.loads(data)
            return prefs if isinstance(prefs, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def update_user_preferences(self, user_id: int, new_prefs: dict) -> None:
        """
        更新用户偏好（增量合并）

        Args:
            user_id: 用户 ID
            new_prefs: 新增/更新的偏好
        """
        if not self.redis:
            return

        existing = self.get_user_preferences(user_id)
        merged = self._merge_preferences(existing, new_prefs)
        merged["last_updated"] = datetime.now().isoformat()

        key = self._preferences_key(user_id)
        # 长期记忆永不过期
        self.redis.set(key, json.dumps(merged, ensure_ascii=False))

    def _merge_preferences(self, existing: dict, new_prefs: dict) -> dict:
        """
        合并偏好数据

        对于列表类型（如 preferred_categories），追加去重；
        对于字典类型（如 price_range），直接覆盖；
        对于标量，直接覆盖。
        """
        merged = existing.copy()

        for key, value in new_prefs.items():
            if key == "last_updated":
                continue

            if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # 列表类型：追加去重
                existing_set = set(merged[key])
                for item in value:
                    existing_set.add(item)
                merged[key] = list(existing_set)
            else:
                # 其他类型：直接覆盖
                merged[key] = value

        return merged

    def extract_preferences_from_messages(self, messages: list[dict]) -> dict:
        """
        从对话历史中提取用户偏好

        简单的规则提取（不依赖 LLM，快速且可控）。
        """
        prefs: dict = {}
        categories: list[str] = []
        brands: list[str] = []

        # 常见品类关键词
        category_keywords = {
            "手机": ["手机", "phone", "iPhone", "智能机"],
            "电脑": ["电脑", "笔记本", "laptop", "台式机", "PC"],
            "平板": ["平板", "iPad", "tablet"],
            "耳机": ["耳机", "earphone", "headphone", "AirPods"],
            "手表": ["手表", "watch", "智能手表"],
            "相机": ["相机", "camera", "单反", "微单"],
            "服装": ["衣服", "服装", "T恤", "裤子", "鞋"],
            "家电": ["冰箱", "洗衣机", "空调", "电视", "家电"],
        }

        # 常见品牌关键词
        brand_keywords = [
            "Apple", "苹果", "华为", "Huawei", "小米", "Xiaomi",
            "三星", "Samsung", "OPPO", "vivo", "联想", "Lenovo",
            "戴尔", "Dell", "索尼", "Sony", "Nike", "阿迪达斯",
        ]

        # 收集所有对话文本
        all_text = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg.get("content"), str)
        )

        # 提取品类
        for category, keywords in category_keywords.items():
            for kw in keywords:
                if kw in all_text:
                    categories.append(category)
                    break

        # 提取品牌
        for brand in brand_keywords:
            if brand.lower() in all_text.lower():
                brands.append(brand)

        # 提取价格区间
        import re
        price_patterns = [
            re.compile(r"(\d+)\s*[-到~]\s*(\d+)\s*元"),
            re.compile(r"(\d+)\s*块"),
            re.compile(r"预算\s*(\d+)"),
        ]
        for pattern in price_patterns:
            match = pattern.search(all_text)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    prefs["price_range"] = {
                        "min": int(groups[0]),
                        "max": int(groups[1]),
                    }
                elif len(groups) == 1:
                    prefs["price_range"] = {"max": int(groups[0])}
                break

        if categories:
            prefs["preferred_categories"] = categories
        if brands:
            prefs["brands"] = brands

        return prefs


# 全局单例
memory_manager = MemoryManager()
