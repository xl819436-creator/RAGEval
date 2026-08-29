"""Day 28：轻量文本向量（词袋 TF，零依赖可复现）。

为什么用词袋：真实场景用 sentence-transformers 之类模型把文本编码成向量，
这里先用最简单的"数每个词出现几次"演示整条链路。
将来接入真 Embedding：只要让 embed(text) 返回模型向量即可，下游代码不用改。
"""

import re
from collections import Counter


class BagOfWords:
    """词袋向量器：把一句话变成"每个词出现次数"的向量。"""

    def __init__(self):
        self.vocab: dict[str, int] = {}   # 词 -> 编号
        self.dimension = 0

    def fit(self, texts: list[str]) -> None:
        """学词表（为什么：先看全部文本有哪些词，给每个词一个固定编号）。"""
        words = set()
        for text in texts:
            words.update(self._tokenize(text))
        self.vocab = {word: idx for idx, word in enumerate(sorted(words))}
        self.dimension = len(self.vocab)

    def embed(self, text: str) -> list[float]:
        """把文本变成向量（每个位置 = 该词出现次数）。"""
        vector = [0.0] * self.dimension
        for word in self._tokenize(text):
            if word in self.vocab:
                vector[self.vocab[word]] += 1.0
        return vector

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """分词（为什么：先变小写，只留字母数字，按空格切开）。"""
        return re.findall(r"[a-z0-9_]+", text.lower())