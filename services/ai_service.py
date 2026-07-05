"""
AI 服务模块

提供智能客服功能：
1. 商品问答（RAG）— 基于商品数据回答用户问题
2. 语义搜索 — 理解用户意图的智能搜索
3. 商品推荐 — 基于相似度的推荐

使用代理 API（通过环境变量配置）
"""

import os
import json
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# AI 客户端配置
_api_key = os.getenv("OPENAI_API_KEY")
_base_url = os.getenv("OPENAI_BASE_URL")

_client = None
if _api_key and OpenAI:
    _kwargs = {"api_key": _api_key}
    if _base_url:
        _kwargs["base_url"] = _base_url
    _client = OpenAI(**_kwargs)


def get_ai_client():
    """获取 AI 客户端"""
    return _client


def is_ai_available() -> bool:
    """检查 AI 服务是否可用"""
    return _client is not None


# ============================================================
# 1. 商品问答（RAG）
# ============================================================

def answer_product_question(question: str, products: list[dict]) -> str:
    """
    基于商品数据回答用户问题（RAG 模式）

    Args:
        question: 用户问题
        products: 从数据库检索到的相关商品列表

    Returns:
        AI 生成的回答
    """
    if not _client:
        return "AI 服务暂不可用，请设置 OPENAI_API_KEY 环境变量"

    # 构建商品上下文
    product_context = "\n".join([
        f"- {p['name']}: ¥{p['price']}，库存 {p['stock']}，{p.get('description', '无描述')}"
        for p in products[:5]  # 最多 5 个商品
    ])

    if not product_context:
        return "抱歉，未找到相关商品信息。"

    # RAG Prompt
    prompt = f"""你是一个专业的电商客服助手。基于以下商品信息回答用户问题。

规则：
1. 只基于提供的商品信息回答，不要编造信息
2. 如果商品信息中没有相关内容，请说"抱歉，我无法根据现有信息回答这个问题"
3. 回答要简洁、专业、友好

商品信息：
{product_context}

用户问题：{question}

回答："""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个专业的电商客服助手。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3  # 客服回答需要稳定
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 服务出错：{str(e)}"


# ============================================================
# 2. 语义搜索
# ============================================================

def semantic_search(query: str, products: list[dict]) -> list[dict]:
    """
    语义搜索：理解用户意图，返回相关商品

    Args:
        query: 用户搜索词
        products: 所有商品列表

    Returns:
        按相关性排序的商品列表
    """
    if not _client:
        # AI 不可用时，回退到简单关键词匹配
        return _keyword_search(query, products)

    # 让 AI 理解用户意图并筛选商品
    product_list = "\n".join([
        f"{i+1}. {p['name']} - {p.get('description', '')}"
        for i, p in enumerate(products[:20])  # 最多处理 20 个
    ])

    prompt = f"""用户搜索："{query}"

以下是商品列表：
{product_list}

请找出与用户搜索最相关的商品，返回商品编号（多个用逗号分隔）。
只返回编号，不要其他文字。

相关商品编号："""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )

        # 解析返回的编号
        indices_str = response.choices[0].message.content.strip()
        indices = []
        for s in indices_str.split(","):
            s = s.strip()
            if s.isdigit():
                idx = int(s) - 1
                if 0 <= idx < len(products):
                    indices.append(idx)

        return [products[i] for i in indices]
    except Exception as e:
        print(f"语义搜索出错：{e}")
        return _keyword_search(query, products)


def _keyword_search(query: str, products: list[dict]) -> list[dict]:
    """简单关键词匹配（回退方案）"""
    query_lower = query.lower()
    return [
        p for p in products
        if query_lower in p['name'].lower() or
           query_lower in p.get('description', '').lower()
    ]


# ============================================================
# 3. 商品推荐
# ============================================================

def recommend_products(product_name: str, all_products: list[dict], limit: int = 3) -> list[dict]:
    """
    商品推荐：基于当前商品推荐相似商品

    Args:
        product_name: 当前商品名称
        all_products: 所有商品列表
        limit: 推荐数量

    Returns:
        推荐的商品列表
    """
    if not _client:
        # AI 不可用时，随机推荐
        return all_products[:limit]

    product_list = "\n".join([
        f"- {p['name']}: {p.get('description', '')}"
        for p in all_products if p['name'] != product_name
    ])

    prompt = f"""用户正在查看："{product_name}"

以下是其他商品：
{product_list}

请推荐 {limit} 个与当前商品相似或相关的商品，返回商品名称（多个用逗号分隔）。
只返回名称，不要其他文字。

推荐商品："""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )

        # 解析返回的商品名称
        names = [n.strip() for n in response.choices[0].message.content.split(",")]
        recommended = []
        for name in names:
            for p in all_products:
                if p['name'] in name and p['name'] != product_name:
                    recommended.append(p)
                    break

        return recommended[:limit] if recommended else all_products[:limit]
    except Exception as e:
        print(f"商品推荐出错：{e}")
        return all_products[:limit]
