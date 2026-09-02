"""Day 32：拒答与引用测试（含实战题 1/2/3）。"""

import pytest

from rageval.answer_pipeline import RAGAnswerPipeline
from rageval.citation import verify_citation


@pytest.fixture(scope="module")
def pipeline():
    """建一次语料索引，多个测试共用（快）。"""
    p = RAGAnswerPipeline(refuse_threshold=0.5)
    p.build_from_manifest("corpus_manifest.json")
    return p


def in_corpus_queries():
    return [
        {"id": "a1", "query": "load_jsonl"},
        {"id": "a2", "query": "calculate_cost"},
        {"id": "a3", "query": "dataset_hash"},
        {"id": "a4", "query": "MockProvider"},
        {"id": "a5", "query": "重试 429"},
        {"id": "a6", "query": "异步调用"},
        {"id": "a7", "query": "exact_match"},
        {"id": "a8", "query": "worker_pool"},
        {"id": "a9", "query": "TokenUsage"},
        {"id": "a10", "query": "validate_dataset"},
    ]


def test_answerable_questions_have_citations(pipeline):
    # 验收：每个可答答案都有引用
    for q in in_corpus_queries():
        response = pipeline.answer(q["query"])
        if not response.refused:
            assert response.answer is not None
            assert len(response.answer.citations) > 0


def test_ten_citations_are_verifiable(pipeline):
    # 实战题 1：10 个可答问题，引用都能回到原文（不指向无关行）
    summary = pipeline.verify_answers(in_corpus_queries())
    assert summary["citations_total"] >= 10
    assert summary["citations_ok"] == summary["citations_total"], summary["bad"]


def test_out_of_corpus_question_refused(pipeline):
    # 实战题 2：语料库外问题应拒答（不做披萨教程）
    response = pipeline.answer("怎么做玛格丽特披萨")
    assert response.refused is True
    assert response.refusal is not None
    assert "阈值" in response.refusal.reason


def test_threshold_high_over_refuses_and_low_rambles():
    # 实战题 3：阈值过高 → 误拒答；阈值过低 → 乱回答（库外问题也答）
    low_pipe = RAGAnswerPipeline(refuse_threshold=0.0)
    low_pipe.build_from_manifest("corpus_manifest.json")
    high_pipe = RAGAnswerPipeline(refuse_threshold=1.01)  # 大于最大置信度 1.0 → 必然误拒
    high_pipe.build_from_manifest("corpus_manifest.json")

    # 阈值 0：库外问题也会被"回答"（乱回答）
    low = low_pipe.answer("怎么做玛格丽特披萨")
    assert low.refused is False
    # 阈值 0.99：正常语料内问题也被拒（误拒答）
    high = high_pipe.answer("load_jsonl")
    assert high.refused is True
    # 阈值 0.5：语料内问题正常回答
    normal = RAGAnswerPipeline(refuse_threshold=0.5)
    normal.build_from_manifest("corpus_manifest.json")
    ok = normal.answer("load_jsonl")
    assert ok.refused is False


def test_config_snapshot_contains_threshold(pipeline):
    # 验收：阈值写入配置快照
    response = pipeline.answer("load_jsonl")
    assert "refuse_threshold" in response.config
    assert "reranker" in response.config


def test_citation_verify_rejects_wrong_lines():
    # 核验函数本身：quote 不在对应行 → False
    from rageval.citation import Citation
    lines = ["line one", "line two", "def target():", "line four"]
    good = Citation(file_path="x.py", symbol_name="target",
                    line_range=(3, 3), quote="def target():")
    bad = Citation(file_path="x.py", symbol_name="target",
                   line_range=(1, 1), quote="def target():")
    assert verify_citation(good, lines) is True
    assert verify_citation(bad, lines) is False
