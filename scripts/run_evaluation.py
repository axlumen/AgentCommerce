"""
RAG 评估脚本

对比优化前（MySQL LIKE）和优化后（三级混合检索）的指标。
运行方式：python scripts/run_evaluation.py
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def retrieve_before(query: str) -> list[int]:
    """优化前：MySQL LIKE 查询"""
    from database import SessionLocal
    from models.product import Product
    from sqlalchemy import or_

    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.is_on_sale == True,
            or_(
                Product.name.contains(query),
                Product.description.contains(query),
            )
        ).limit(5).all()
        return [p.id for p in products]
    finally:
        db.close()


def retrieve_after(query: str) -> list[int]:
    """优化后：三级混合检索"""
    from rag.retriever import get_retriever, fallback_search

    retriever = get_retriever()

    # 检查索引是否已构建
    status = retriever.get_status()
    if status["mode"] == "fallback":
        # 降级搜索
        results = fallback_search(query, top_k=5)
        return [r["id"] for r in results]

    try:
        results = retriever.search(query, top_k=5)
        return [r.product_id for r in results]
    except Exception as e:
        print(f"  [WARN] Hybrid search failed: {e}, falling back")
        results = fallback_search(query, top_k=5)
        return [r["id"] for r in results]


def build_indexes():
    """构建检索索引"""
    from database import SessionLocal
    from models.product import Product
    from rag.retriever import get_retriever

    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.is_on_sale == True).all()
        product_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description or "",
                "price": float(p.price),
                "stock": p.stock,
                "category_id": p.category_id,
                "brand": p.brand or "",
                "specs": p.specs or {},
            }
            for p in products
        ]

        if not product_dicts:
            print("[WARN] No products in database. Using mock data for evaluation.")
            return False

        retriever = get_retriever()
        retriever.build_index(product_dicts)
        return True
    finally:
        db.close()


def main():
    print("=" * 60)
    print("RAG 评估脚本")
    print("=" * 60)

    # 检查测试集
    test_set_path = project_root / "data" / "test_set.json"
    if not test_set_path.exists():
        print(f"[ERROR] Test set not found: {test_set_path}")
        sys.exit(1)

    # 构建索引
    print("\n[1/3] 构建检索索引...")
    has_index = build_indexes()

    # 运行评估
    print("\n[2/3] 运行评估...")
    from rag.evaluation import run_evaluation

    output_path = project_root / "data" / "evaluation_report.json"
    report = run_evaluation(
        test_set_path=str(test_set_path),
        retrieve_before_fn=retrieve_before,
        retrieve_after_fn=retrieve_after,
        output_path=str(output_path),
    )

    print(f"\n[3/3] 评估完成！报告已保存到: {output_path}")

    # 显示改进摘要
    b = report.metrics_before
    a = report.metrics_after
    if a.recall_at_5 > b.recall_at_5:
        print(f"\n✅ Recall@5 提升: {a.recall_at_5 - b.recall_at_5:+.4f}")
    if a.ndcg_at_5 > b.ndcg_at_5:
        print(f"✅ NDCG@5 提升: {a.ndcg_at_5 - b.ndcg_at_5:+.4f}")


if __name__ == "__main__":
    main()
