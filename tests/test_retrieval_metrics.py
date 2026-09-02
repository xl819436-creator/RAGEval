"""Day 33：检索指标测试（含实战题 1、2 与手算核对）。"""

import pytest

from rageval.retrieval_metrics import (
    dcg_at_k,
    idcg_at_k,
    mrr,
    ndcg_at_k,
    p95_latency,
    recall_at_k,
    reciprocal_rank,
)


def test_reciprocal_rank_at_third_position():
    # 实战题 1：相关块在第 3 位 → 1/3
    ranked = ["a", "b", "c", "d"]
    assert reciprocal_rank(ranked, {"c"}) == pytest.approx(1 / 3)


def test_reciprocal_rank_at_first_and_fifth():
    assert reciprocal_rank(["x", "y"], {"x"}) == 1.0
    assert reciprocal_rank(["a", "b", "c", "d", "e"], {"e"}) == pytest.approx(1 / 5)


def test_reciprocal_rank_not_found_is_zero():
    assert reciprocal_rank(["a", "b"], {"z"}) == 0.0


def test_recall_at_k():
    # relevant 两个块，前 5 只命中 1 个 → 0.5
    ranked = ["a", "b", "c", "d", "e"]
    assert recall_at_k(ranked, {"a", "z"}, k=5) == 0.5
    assert recall_at_k(ranked, {"a"}, k=3) == 1.0
    assert recall_at_k(ranked, {"z"}, k=5) == 0.0


def test_no_answer_question_has_no_relevant():
    # 实战题 2：无答案问题 relevant 为空，不产生任意命中
    ranked = ["a", "b", "c"]
    assert recall_at_k(ranked, set(), k=5) == 0.0
    assert reciprocal_rank(ranked, set()) == 0.0
    assert ndcg_at_k(ranked, set(), k=5) == 0.0


def test_mrr_average():
    # q1 相关排第 1（1.0），q2 相关排第 3（1/3）→ MRR = (1 + 1/3)/2
    result = mrr([(["a", "b"], {"a"}), (["x", "y", "c"], {"c"})])
    assert result == pytest.approx((1.0 + 1 / 3) / 2)


def test_ndcg_hand_calculated():
    # 手算：ranked=[a,b,c,d,e]，relevant={c}，k=5
    # DCG = 1/log2(4) = 0.5；IDCG = 1/log2(2) = 1.0 → NDCG = 0.5
    ranked = ["a", "b", "c", "d", "e"]
    assert dcg_at_k(ranked, {"c"}, 5) == pytest.approx(1 / 2)
    assert idcg_at_k(1, 5) == pytest.approx(1.0)
    assert ndcg_at_k(ranked, {"c"}, 5) == pytest.approx(0.5)


def test_ndcg_perfect_rank_is_one():
    # 相关块恰好排最前 → NDCG=1
    ranked = ["c", "a", "b"]
    assert ndcg_at_k(ranked, {"c"}, 3) == pytest.approx(1.0)


def test_p95_latency():
    values = list(range(1, 101))  # 1..100
    assert p95_latency(values) == pytest.approx(95.05)
    assert p95_latency([]) == 0.0
