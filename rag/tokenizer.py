"""
中文分词器

职责：
- jieba 分词 + 电商停用词过滤
- 同义词扩展（手机=智能手机=移动电话）
- 搜索用分词（含同义词扩展）
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# jieba 延迟初始化
_jieba = None


def _get_jieba():
    global _jieba
    if _jieba is None:
        try:
            import jieba
            jieba.setLogLevel(logging.WARNING)
            _jieba = jieba
        except ImportError:
            logger.warning("jieba not installed, tokenization will use simple split")
            _jieba = False
    return _jieba


# 电商停用词（精简版，保留有检索意义的词）
STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
    "吗", "把", "那", "被", "从", "们", "但", "又", "对", "它",
    "吗", "什么", "怎么", "怎样", "如何", "哪些", "哪个", "多少",
    "请", "帮", "帮忙", "想", "需要", "看看", "看看", "一下",
    "可以", "能", "能够", "是否", "有没有", "有没有",
}

# 电商同义词表
DEFAULT_SYNONYMS = {
    "手机": ["智能手机", "移动电话", "phone"],
    "智能手机": ["手机", "移动电话"],
    "笔记本": ["笔记本电脑", "laptop"],
    "笔记本电脑": ["笔记本", "laptop"],
    "电脑": ["计算机", "PC", "个人电脑"],
    "平板": ["平板电脑", "tablet", "iPad"],
    "耳机": ["耳麦", "earphone", "headphone"],
    "无线耳机": ["蓝牙耳机", "真无线耳机", "TWS"],
    "手表": ["智能手表", "smartwatch"],
    "电视": ["电视机", "TV"],
    "冰箱": ["冷藏柜"],
    "洗衣机": ["洗衣服的机器"],
    "空调": ["冷气机"],
    "相机": ["照相机", "摄像机"],
    "单反": ["单反相机", "DSLR"],
    "微单": ["无反相机", "微单相机"],
    "衣服": ["服装", "服饰"],
    "鞋": ["鞋子", "运动鞋"],
    "包": ["包包", "手提包", "背包"],
    "化妆品": ["护肤品", "美妆"],
    "洗面奶": ["洁面乳", "洗面乳"],
    "口红": ["唇膏", "唇釉"],
    "粉底": ["粉底液", "底妆"],
    "性价比高": ["便宜", "实惠", "划算"],
    "好用": ["好使", "不错", "好"],
    "拍照好": ["摄像好", "相机好", "拍照清晰"],
    "大屏": ["大屏幕", "大尺寸"],
    "轻薄": ["薄", "轻便", "便携"],
    "续航长": ["电池耐用", "待机长", "电量持久"],
    "快充": ["快速充电", "闪充"],
    "游戏": ["手游", "打游戏"],
    "办公": ["商务", "工作"],
    "学生": ["学习", "校园"],
}


class Tokenizer:
    """中文分词器"""

    def __init__(self, synonym_path: str | None = None):
        self._synonyms: dict[str, list[str]] = {}
        self._reverse_synonyms: dict[str, set[str]] = {}
        self._load_synonyms(synonym_path)

    def _load_synonyms(self, path: str | None) -> None:
        """加载同义词表"""
        synonyms = dict(DEFAULT_SYNONYMS)

        # 尝试从文件加载
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_synonyms = json.load(f)
                synonyms.update(file_synonyms)
                logger.info(f"Loaded {len(file_synonyms)} synonym entries from {path}")
            except Exception as e:
                logger.warning(f"Failed to load synonyms from {path}: {e}")

        self._synonyms = synonyms

        # 构建反向索引：每个词 → 它的所有同义词
        self._reverse_synonyms = {}
        for key, values in synonyms.items():
            all_terms = {key} | set(values)
            for term in all_terms:
                if term not in self._reverse_synonyms:
                    self._reverse_synonyms[term] = set()
                self._reverse_synonyms[term] |= all_terms - {term}

    def tokenize(self, text: str) -> list[str]:
        """
        分词 + 去停用词

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        if not text:
            return []

        jieba = _get_jieba()
        if jieba:
            tokens = list(jieba.cut(text))
        else:
            # jieba 不可用时，简单按字符分割（中文）或空格分割（英文）
            tokens = self._simple_tokenize(text)

        # 去停用词 + 去空格
        return [t.strip() for t in tokens if t.strip() and t.strip() not in STOPWORDS]

    def expand_synonyms(self, tokens: list[str]) -> list[str]:
        """
        同义词扩展

        Args:
            tokens: 原始分词结果

        Returns:
            扩展后的分词结果（含同义词）
        """
        expanded = list(tokens)
        for token in tokens:
            synonyms = self._reverse_synonyms.get(token, set())
            expanded.extend(synonyms)
        return list(set(expanded))

    def tokenize_for_search(self, text: str) -> list[str]:
        """
        搜索用分词（分词 + 去停用词 + 同义词扩展）

        Args:
            text: 搜索文本

        Returns:
            扩展后的分词结果
        """
        tokens = self.tokenize(text)
        return self.expand_synonyms(tokens)

    def _simple_tokenize(self, text: str) -> list[str]:
        """简单分词（jieba 不可用时的降级方案）"""
        import re
        # 中文按字符分割，英文按空格分割
        tokens = []
        for part in re.findall(r'[一-鿿]|[a-zA-Z0-9]+', text):
            tokens.append(part)
        return tokens


# 全局单例
_tokenizer: Tokenizer | None = None


def get_tokenizer() -> Tokenizer:
    """获取分词器单例"""
    global _tokenizer
    if _tokenizer is None:
        from config import RAG_SYNONYM_PATH
        _tokenizer = Tokenizer(synonym_path=RAG_SYNONYM_PATH)
    return _tokenizer
