"""Day 31：RRF 单元测试（含实战题 2 手算核对、实战题 3 k 敏感性）。"""

import pytest

from rageval.rrf import reciprocal_rank_fusion


def test_rrf_hand_calculated_two_rankings():
    # 实战题 2：手算两条排名的 RRF（k=60）
    # ranking1 = [A, B, C]，ranking2 = [B, A, C]
    # A: 1/61 + 1/62 ≈ 0.03250
    # B: 1/62 + 1/61 ≈ 0.03250（A、B 平分，实际 A 与 B 相同）
    # C: 1/63 + 1/63 ≈ 0.03175
    fused = reciprocal_rank_fusion([["A", "B", "C"], ["B", "A", "C"]], k=60)
    scores = dict(fused)
    assert scores["A"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["B"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["C"] == pytest.approx(1 / 63 + 1 / 63)
    # A 和 B 同分，谁在前取决于排序稳定性；都排在 C 前面
    assert scores["A"] > scores["C"]
    assert scores["B"] > scores["C"]


def test_rrf_better_rank_gets_higher_score():
    # 同一路里排得越靠前，RRF 分越高
    fused = reciprocal_rank_fusion([["X", "Y", "Z"]], k=60)
    scores = dict(fused)
    assert scores["X"] > scores["Y"] > scores["Z"]


def test_rrf_k_sensitivity():
    # 实战题 3：改变 k，排名可能变化但"排得越前分越高"的性质不变
    small_k = reciprocal_rank_fusion([["A", "B", "C"]], k=1)
    large_k = reciprocal_rank_fusion([["A", "B", "C"]], k=100)
    assert dict(small_k)["A"] > dict(small_k)["B"]
    assert dict(large_k)["A"] > dict(large_k)["B"]
    # k 越大，同一排名的分越小
    assert dict(small_k)["A"] > dict(large_k)["A"]


def test_rrf_union_of_all_ranked_items():
    # 融合结果应包含各路出现过的所有 chunk_id
    fused = reciprocal_rank_fusion([["A", "B"], ["C"]], k=60)
    ids = {cid for cid, _ in fused}
    assert ids == {"A", "B", "C"}
