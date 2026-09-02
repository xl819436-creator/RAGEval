"""Day 32：Reranker 接口与 MockReranker。

为什么先 Mock 再接真模型：接口先行，BGE-reranker 等真实模型只需替换
MockReranker 的实现（同样返回 score），管道与测试都不用改。
"""

from dataclasses import dataclass
import re

from rageval.vector_index import SearchHit


def tokenize(text: str) -> list[str]:
    """分词规则：与 embeddings.BagOfWords 一致（小写 + 字母数字下划线）。

    为什么在这里自带一份而不是 import：reranker 是 Day 32 独立模块，
    不依赖任何未合并的模块，保证在干净分支上也能直接跑。
    """
    return re.findall(r"[a-z0-9_]+", text.lower())


@dataclass
class Candidate:
    """初召回的一条候选：检索命中 + 原文 + 符号名（供重排与引用使用）。"""

    hit: SearchHit
    text: str
    symbol_name: str | None = None


@dataclass
class ScoredCandidate:
    """重排后的候选：带上重排分数。"""

    candidate: Candidate
    rerank_score: float


class BaseReranker:
    """重排器接口：对初召回候选重新打分排序。"""

    def rerank(self, query: str, candidates: list[Candidate]) -> list[ScoredCandidate]:
        raise NotImplementedError


class MockReranker(BaseReranker):
    """模拟重排器：按"查询词在候选文本里的覆盖率"打分。

    覆盖率 = 查询词里有多少个出现在候选文本中（0~1）。
    这模拟真实 Reranker 做的"更精细相关性打分"；换 BGE 时只改这里。
    """

    def rerank(self, query: str, candidates: list[Candidate]) -> list[ScoredCandidate]:
        query_tokens = set(tokenize(query))
        scored = []
        for candidate in candidates:
            text_tokens = set(tokenize(candidate.text))
            if query_tokens:
                coverage = len(query_tokens & text_tokens) / len(query_tokens)
            else:
                coverage = 0.0
            scored.append(ScoredCandidate(candidate=candidate, rerank_score=coverage))
        scored.sort(key=lambda item: item.rerank_score, reverse=True)
        return scored
