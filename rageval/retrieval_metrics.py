"""Day 33：检索评估指标——Recall@K、MRR、NDCG@K、P95 延迟。

全部为纯函数，方便单测与手算核对（验收：5 条手算一致）。
约定：relevant 为空（无答案问题）时不参与指标计算，由调用方跳过。
"""

import math
from typing import Iterable, Optional


def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Recall@K：前 k 个结果里命中了多少个相关块 ÷ 相关块总数。

    例子：relevant={A,B}，前 5 命中 {A} → 1/2 = 0.5
    """
    if not relevant_ids:
        return 0.0
    hit = sum(1 for cid in ranked_ids[:k] if cid in relevant_ids)
    return hit / len(relevant_ids)


def reciprocal_rank(ranked_ids: list[str], relevant_ids: set[str]) -> float:
    """第一个相关块排在第几位，取倒数；没找到返回 0。

    实战题 1：相关块在第 3 位 → 1/3 ≈ 0.333
    """
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def mrr(queries_results: list[tuple[list[str], set[str]]]) -> float:
    """MRR：所有查询 reciprocal rank 的平均。"""
    if not queries_results:
        return 0.0
    return sum(reciprocal_rank(ranked, relevant) for ranked, relevant in queries_results) / len(queries_results)


def dcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """DCG@K：Σ rel_i / log2(i+1)，rel_i=1 当第 i 个结果相关（位置 1 起）。"""
    return sum(
        1.0 / math.log2(i + 1)
        for i, cid in enumerate(ranked_ids[:k], start=1)
        if cid in relevant_ids
    )


def idcg_at_k(relevant_count: int, k: int) -> float:
    """IDCG@K：理想排序（相关块排最前）下的 DCG。"""
    return sum(1.0 / math.log2(i + 1) for i in range(1, min(relevant_count, k) + 1))


def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """NDCG@K = DCG / IDCG（0~1；排序完美时 = 1）。"""
    if not relevant_ids:
        return 0.0
    ideal = idcg_at_k(len(relevant_ids), k)
    if ideal == 0:
        return 0.0
    return dcg_at_k(ranked_ids, relevant_ids, k) / ideal


def p95_latency(latencies_ms: list[float]) -> float:
    """P95 延迟：95% 的查询不超过该值；空列表返回 0。"""
    if not latencies_ms:
        return 0.0
    sorted_values = sorted(latencies_ms)
    index = (len(sorted_values) - 1) * 0.95
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = index - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac
