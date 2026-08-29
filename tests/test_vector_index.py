"""Day 30：向量索引测试（实战题 1/2 + 稳定排序 + 字段完整）。"""

import pytest

from rageval.embeddings import BagOfWords
from rageval.vector_index import VectorIndex


def make_index(texts: list[str]) -> VectorIndex:
    bow = BagOfWords()
    bow.fit(texts)
    index = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    chunks = [
        {"chunk_id": f"c{i}", "file_path": f"f{i}.py",
         "start_line": 1, "end_line": 3, "text": text}
        for i, text in enumerate(texts)
    ]
    index.build(chunks)
    return index


def test_search_returns_fields_and_sorted():
    index = make_index(["def load_jsonl(file):", "class MockProvider:", "def load_jsonl(path):"])
    results = index.vector_search("load_jsonl", top_k=3)
    assert len(results) == 3
    for hit in results:
        assert hit.chunk_id and hit.file_path and hit.line_range and hit.score >= 0
    # 稳定排序：分数从高到低
    scores = [hit.score for hit in results]
    assert scores == sorted(scores, reverse=True)


def test_top_k_larger_than_index_does_not_error():
    # 实战题 1：top_k 大于索引数量时不报错，返回全部
    index = make_index(["a", "b"])
    results = index.vector_search("a", top_k=999)
    assert len(results) == 2


def test_empty_query_rejected():
    # 实战题 2：空查询被拒绝
    index = make_index(["a"])
    with pytest.raises(ValueError, match="查询不能为空"):
        index.vector_search("   ")


def test_same_content_scores_one():
    index = make_index(["def load():", "def load():", "class X:"])
    results = index.vector_search("def load():", top_k=3)
    assert results[0].score == pytest.approx(1.0)  # 完全相同的文本，相似度 = 1