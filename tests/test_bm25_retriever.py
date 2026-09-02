"""Day 31：BM25 检索器测试（含实战题 1：函数名精确查询 BM25 应更靠前）。"""

import pytest

from rageval.bm25_retriever import BM25Retriever


def make_chunks():
    return [
        {"chunk_id": "loader.py:13-91", "file_path": "loader.py",
         "start_line": 13, "end_line": 91, "text": "def load_jsonl(file_path): 读取 JSONL 数据集"},
        {"chunk_id": "cost.py:1-30", "file_path": "cost.py",
         "start_line": 1, "end_line": 30, "text": "def calculate_cost(prompt_tokens): 计算调用成本"},
        {"chunk_id": "provider.py:1-40", "file_path": "provider.py",
         "start_line": 1, "end_line": 40, "text": "class MockProvider: 模拟模型响应"},
        {"chunk_id": "loader.py:1-12", "file_path": "loader.py",
         "start_line": 1, "end_line": 12, "text": "import json 数据集加载辅助"},
    ]


def test_bm25_returns_searchhit_fields():
    retriever = BM25Retriever()
    retriever.build(make_chunks())
    hits = retriever.search("load_jsonl", top_k=3)
    assert len(hits) == 3
    for hit in hits:
        assert hit.chunk_id and hit.file_path and hit.line_range
        assert hit.score >= 0


def test_bm25_exact_function_name_ranks_first():
    # 实战题 1：函数名精确查询，BM25 把含该词最多的文档排最前
    retriever = BM25Retriever()
    retriever.build(make_chunks())
    hits = retriever.search("load_jsonl", top_k=4)
    assert hits[0].file_path == "loader.py"


def test_bm25_empty_query_rejected():
    retriever = BM25Retriever()
    retriever.build(make_chunks())
    with pytest.raises(ValueError, match="查询不能为空"):
        retriever.search("   ")


def test_bm25_top_k_larger_than_index():
    retriever = BM25Retriever()
    retriever.build(make_chunks())
    hits = retriever.search("load_jsonl", top_k=999)
    assert len(hits) == 4  # 不报错，返回全部
