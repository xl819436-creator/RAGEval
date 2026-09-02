"""Day 31：BM25 检索器（自己实现 BM25Okapi，零依赖）。

为什么自己实现而不是用 rank-bm25 库：①该包在当前网络下装不上；
②自己实现可以复用与 BagOfWords 完全相同的分词规则，三路对比（向量/BM25/RRF）才公平；
③纯 Python、公式透明、可复现。
"""

import math
import re
from collections import Counter
from typing import Optional

from rageval.vector_index import SearchHit


def tokenize(text: str) -> list[str]:
    """分词规则：与 BagOfWords 完全一致（小写 + 只留字母数字下划线）。

    为什么必须一致：三路检索用同一套分词，比的才是"检索算法"而不是"分词器"。
    """
    return re.findall(r"[a-z0-9_]+", text.lower())


class BM25Retriever:
    """BM25Okapi 检索器（k1=1.5, b=0.75 是标准默认参数）。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._chunks: list[dict] = []
        self._tokenized_docs: list[list[str]] = []
        self._doc_len: list[int] = []
        self._doc_freq: dict[str, int] = {}
        self._avgdl: float = 0.0
        self._total: int = 0

    def build(self, chunks: list[dict]) -> None:
        """chunks 与 VectorIndex.build 同一协议：{chunk_id, file_path, start_line, end_line, text}"""
        self._chunks = list(chunks)
        self._total = len(chunks)
        self._doc_len = []
        self._tokenized_docs = []
        doc_freq: dict[str, int] = {}
        for chunk in self._chunks:
            tokens = tokenize(chunk["text"])
            self._tokenized_docs.append(tokens)
            self._doc_len.append(len(tokens))
            for token in set(tokens):
                doc_freq[token] = doc_freq.get(token, 0) + 1
        self._doc_freq = doc_freq
        self._avgdl = sum(self._doc_len) / self._total if self._total else 0.0

    def search(self, query: str, top_k: int = 10) -> list[SearchHit]:
        """Top-K 检索：返回 SearchHit，与 VectorIndex.vector_search 同协议。"""
        if not query.strip():
            raise ValueError("查询不能为空")
        query_tokens = tokenize(query)
        scores = [self._score(query_tokens, doc_idx) for doc_idx in range(self._total)]
        ranked = sorted(range(self._total), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            SearchHit(
                chunk_id=self._chunks[i]["chunk_id"],
                file_path=self._chunks[i]["file_path"],
                line_range=(self._chunks[i]["start_line"], self._chunks[i]["end_line"]),
                score=round(scores[i], 6),
            )
            for i in ranked
        ]

    def _score(self, query_tokens: list[str], doc_idx: int) -> float:
        """BM25 公式：对查询里每个词，idf * 词频折损，累加。"""
        doc_tokens = self._tokenized_docs[doc_idx]
        freq = Counter(doc_tokens)
        dl = self._doc_len[doc_idx]
        score = 0.0
        for token in set(query_tokens):
            df = self._doc_freq.get(token, 0)
            if df == 0:
                continue
            f = freq.get(token, 0)
            if f == 0:
                continue
            idf = math.log(1 + (self._total - df + 0.5) / (df + 0.5))
            tf_part = (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self._avgdl))
            score += idf * tf_part
        return score
