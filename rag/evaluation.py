"""
RAG 评估框架

指标：
- Recall@K：召回率@K
- Precision@K：准确率@K
- NDCG@K：归一化折损累积增益
- 回答相关性：LLM 评分或简单匹配
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field
from datetime import datetime

from rag.exceptions import EvaluationError

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例"""
    id: int
    question: str
    standard_answer: str
    relevant_product_ids: list[int]
    intent: str = ""           # recommendation, search, comparison, etc.
    category: str = ""         # 手机, 电脑, etc.


@dataclass
class RetrievalMetrics:
    """检索指标"""
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_5: float = 0.0
    ndcg_at_5: float = 0.0
    avg_latency_ms: float = 0.0


@dataclass
class EvaluationReport:
    """评估报告"""
    timestamp: str = ""
    test_set_size: int = 0
    metrics_before: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    metrics_after: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    per_query_results: list[dict] = field(default_factory=list)


def recall_at_k(retrieved_ids: list[int], relevant_ids: list[int], k: int) -> float:
    """
    召回率@K

    Args:
        retrieved_ids: 检索到的商品 ID 列表（按相关性排序）
        relevant_ids: 相关商品 ID 列表
        k: 截断位置

    Returns:
        召回率 [0, 1]
    """
    if not relevant_ids:
        return 0.0
    retrieved_at_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)
    hits = len(retrieved_at_k & relevant)
    return hits / len(relevant)


def precision_at_k(retrieved_ids: list[int], relevant_ids: list[int], k: int) -> float:
    """
    准确率@K

    Args:
        retrieved_ids: 检索到的商品 ID 列表
        relevant_ids: 相关商品 ID 列表
        k: 截断位置

    Returns:
        准确率 [0, 1]
    """
    if k == 0:
        return 0.0
    retrieved_at_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)
    hits = len(retrieved_at_k & relevant)
    return hits / k


def ndcg_at_k(retrieved_ids: list[int], relevant_ids: list[int], k: int) -> float:
    """
    NDCG@K（归一化折损累积增益）

    Args:
        retrieved_ids: 检索到的商品 ID 列表
        relevant_ids: 相关商品 ID 列表（所有相关文档的相关性为 1）
        k: 截断位置

    Returns:
        NDCG [0, 1]
    """
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return 0.0

    # DCG
    dcg = 0.0
    for i, pid in enumerate(retrieved_ids[:k]):
        if pid in relevant_set:
            dcg += 1.0 / math.log2(i + 2)  # i+2 因为 log2(1) = 0

    # IDCG（理想排序）
    idcg = 0.0
    for i in range(min(len(relevant_set), k)):
        idcg += 1.0 / math.log2(i + 2)

    return dcg / idcg if idcg > 0 else 0.0


def load_test_set(path: str) -> list[TestCase]:
    """
    加载测试集

    Args:
        path: 测试集文件路径（JSON 或 CSV）

    Returns:
        TestCase 列表
    """
    if not os.path.exists(path):
        raise EvaluationError(f"Test set not found: {path}")

    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            TestCase(
                id=item["id"],
                question=item["question"],
                standard_answer=item["standard_answer"],
                relevant_product_ids=item["relevant_product_ids"],
                intent=item.get("intent", ""),
                category=item.get("category", ""),
            )
            for item in data
        ]
    elif path.endswith(".csv"):
        import csv
        cases = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cases.append(TestCase(
                    id=int(row["id"]),
                    question=row["question"],
                    standard_answer=row["standard_answer"],
                    relevant_product_ids=json.loads(row["relevant_product_ids"]),
                    intent=row.get("intent", ""),
                    category=row.get("category", ""),
                ))
        return cases
    else:
        raise EvaluationError(f"Unsupported test set format: {path}")


def evaluate_retrieval(
    test_cases: list[TestCase],
    retrieve_fn,
    k: int = 5,
) -> RetrievalMetrics:
    """
    评估检索质量

    Args:
        test_cases: 测试用例列表
        retrieve_fn: 检索函数，签名 fn(query) -> list[int]（返回商品 ID 列表）
        k: 评估截断位置

    Returns:
        检索指标
    """
    import time

    total_recall = 0.0
    total_precision = 0.0
    total_ndcg = 0.0
    total_latency = 0.0
    valid_count = 0

    for case in test_cases:
        try:
            start = time.time()
            retrieved_ids = retrieve_fn(case.question)
            latency = (time.time() - start) * 1000

            total_recall += recall_at_k(retrieved_ids, case.relevant_product_ids, k)
            total_precision += precision_at_k(retrieved_ids, case.relevant_product_ids, k)
            total_ndcg += ndcg_at_k(retrieved_ids, case.relevant_product_ids, k)
            total_latency += latency
            valid_count += 1
        except Exception as e:
            logger.warning(f"Failed to evaluate case {case.id}: {e}")

    if valid_count == 0:
        return RetrievalMetrics()

    return RetrievalMetrics(
        recall_at_5=total_recall / valid_count,
        precision_at_5=total_precision / valid_count,
        ndcg_at_5=total_ndcg / valid_count,
        avg_latency_ms=total_latency / valid_count,
    )


def run_evaluation(
    test_set_path: str,
    retrieve_before_fn,
    retrieve_after_fn,
    output_path: str | None = None,
) -> EvaluationReport:
    """
    运行完整评估（优化前 vs 优化后）

    Args:
        test_set_path: 测试集路径
        retrieve_before_fn: 优化前检索函数
        retrieve_after_fn: 优化后检索函数
        output_path: 报告输出路径（可选）

    Returns:
        评估报告
    """
    test_cases = load_test_set(test_set_path)
    logger.info(f"Loaded {len(test_cases)} test cases")

    # 评估优化前
    logger.info("Evaluating before optimization...")
    metrics_before = evaluate_retrieval(test_cases, retrieve_before_fn, k=5)

    # 评估优化后
    logger.info("Evaluating after optimization...")
    metrics_after = evaluate_retrieval(test_cases, retrieve_after_fn, k=5)

    # 构建报告
    report = EvaluationReport(
        timestamp=datetime.now().isoformat(),
        test_set_size=len(test_cases),
        metrics_before=metrics_before,
        metrics_after=metrics_after,
    )

    # 计算每个查询的详细结果
    for case in test_cases:
        try:
            before_ids = retrieve_before_fn(case.question)
            after_ids = retrieve_after_fn(case.question)
            report.per_query_results.append({
                "id": case.id,
                "question": case.question,
                "relevant_ids": case.relevant_product_ids,
                "before_ids": before_ids[:5],
                "after_ids": after_ids[:5],
                "before_recall": recall_at_k(before_ids, case.relevant_product_ids, 5),
                "after_recall": recall_at_k(after_ids, case.relevant_product_ids, 5),
            })
        except Exception as e:
            logger.debug(f"Failed to evaluate case {case.id}: {e}")

    # 输出报告
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_report_to_dict(report), f, ensure_ascii=False, indent=2)
        logger.info(f"Evaluation report saved to {output_path}")

    # 打印摘要
    _print_summary(report)

    return report


def _report_to_dict(report: EvaluationReport) -> dict:
    """报告转字典"""
    return {
        "timestamp": report.timestamp,
        "test_set_size": report.test_set_size,
        "metrics_before": {
            "recall_at_5": report.metrics_before.recall_at_5,
            "precision_at_5": report.metrics_before.precision_at_5,
            "ndcg_at_5": report.metrics_before.ndcg_at_5,
            "avg_latency_ms": report.metrics_before.avg_latency_ms,
        },
        "metrics_after": {
            "recall_at_5": report.metrics_after.recall_at_5,
            "precision_at_5": report.metrics_after.precision_at_5,
            "ndcg_at_5": report.metrics_after.ndcg_at_5,
            "avg_latency_ms": report.metrics_after.avg_latency_ms,
        },
        "improvement": {
            "recall_at_5": report.metrics_after.recall_at_5 - report.metrics_before.recall_at_5,
            "precision_at_5": report.metrics_after.precision_at_5 - report.metrics_before.precision_at_5,
            "ndcg_at_5": report.metrics_after.ndcg_at_5 - report.metrics_before.ndcg_at_5,
        },
        "per_query_results": report.per_query_results,
    }


def _print_summary(report: EvaluationReport) -> None:
    """打印评估摘要"""
    b = report.metrics_before
    a = report.metrics_after

    lines = [
        "",
        "=" * 60,
        "RAG 评估报告",
        "=" * 60,
        f"测试集大小: {report.test_set_size}",
        f"时间: {report.timestamp}",
        "-" * 60,
        f"{'指标':<20} {'优化前':>10} {'优化后':>10} {'提升':>10}",
        "-" * 60,
        f"{'Recall@5':<20} {b.recall_at_5:>10.4f} {a.recall_at_5:>10.4f} {a.recall_at_5 - b.recall_at_5:>+10.4f}",
        f"{'Precision@5':<20} {b.precision_at_5:>10.4f} {a.precision_at_5:>10.4f} {a.precision_at_5 - b.precision_at_5:>+10.4f}",
        f"{'NDCG@5':<20} {b.ndcg_at_5:>10.4f} {a.ndcg_at_5:>10.4f} {a.ndcg_at_5 - b.ndcg_at_5:>+10.4f}",
        f"{'Avg Latency (ms)':<20} {b.avg_latency_ms:>10.1f} {a.avg_latency_ms:>10.1f} {a.avg_latency_ms - b.avg_latency_ms:>+10.1f}",
        "=" * 60,
    ]
    logger.info("\n".join(lines))
