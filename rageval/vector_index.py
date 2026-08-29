"""Day 30：向量索引——把语料块向量化，按余弦相似度做 Top-K 检索。

为什么叫"向量索引"：真实系统会用倒排索引 / ANN（如 FAISS）加速，
教学版先做最朴素的"暴力检索"：查询和每个块都算一遍余弦相似度，取最高 Top-K。
块少时完全够用，且每一步都可追溯。
"""

from dataclasses import dataclass

from rageval.cosine import cosine_similarity


@dataclass
class SearchHit:
    """一条检索结果：块 + 可追溯位置 + 相似度分数。"""

    chunk_id: str  # 块编号
    file_path: str  # 原始文件路径（可追溯）
    line_range: tuple[int, int]  # 行号范围 (start_line, end_line)（可追溯）
    score: float  # 与查询的余弦相似度（0~1，越大越相关）


class VectorIndex:
    """向量索引：build() 建索引，vector_search() 做 Top-K 检索。"""

    def __init__(
        self,
        embedding_model: str = "bag-of-words-tf",
        embed_fn=None,
    ):
        """embedding_model：给索引起个名字，记录用的是哪种向量器；
        embed_fn：text -> vector 的函数（如 BagOfWords.embed），
        将来换真 Embedding 模型时只需换这个函数，下游不用改。"""
        if embed_fn is None:
            raise ValueError("embed_fn 不能为空，请传入一个 text -> vector 的函数")
        self.embedding_model = embedding_model
        self._embed_fn = embed_fn
        self._chunks: list[dict] = []
        self._vectors: list[list[float]] = []

    def build(self, chunks: list[dict]) -> None:
        """把所有块向量化，建立索引。

        chunks 是 list[dict]，每项必须含：
        chunk_id / file_path / start_line / end_line / text
        """
        self._chunks = list(chunks)
        self._vectors = [self._embed_fn(c["text"]) for c in self._chunks]

    def manifest(self) -> dict:
        """索引元信息（可追溯/可复现）：向量器、块数、向量维度。"""
        return {
            "embedding_model": self.embedding_model,
            "chunk_count": len(self._chunks),
            "dimension": len(self._vectors[0]) if self._vectors else 0,
        }

    def vector_search(self, query: str, top_k: int = 10) -> list[SearchHit]:
        """把查询向量化，与每个块算余弦相似度，返回分数最高的 top_k 条（降序）。

        - 空查询（含全空格）拒绝：raise ValueError("查询不能为空")
        - top_k 大于索引数量：不报错，返回全部
        - 排序稳定：同分时保持原先后顺序
        """
        if not query.strip():
            raise ValueError("查询不能为空")

        qv = self._embed_fn(query)
        scored = [
            (cosine_similarity(qv, vec), chunk)
            for chunk, vec in zip(self._chunks, self._vectors)
        ]
        scored.sort(key=lambda item: item[0], reverse=True)  # 分数从高到低（稳定排序）

        return [
            SearchHit(
                chunk_id=chunk["chunk_id"],
                file_path=chunk["file_path"],
                line_range=(chunk["start_line"], chunk["end_line"]),
                score=score,
            )
            for score, chunk in scored[:top_k]
        ]
