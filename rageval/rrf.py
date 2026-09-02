"""Day 31：Reciprocal Rank Fusion（RRF）——多路排名融合。

为什么不能用"直接把原始分数相加"：不同检索器的分数量纲不同（向量是 0~1 余弦，
BM25 可以到几十上百），直接相加会被分数大的那一路带偏。
RRF 只按"排名"打分：排第几名就给 1/(k+rank) 分，量纲统一、公平。
"""


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """把多路"已排序的 chunk_id 列表"融合成一个排序。

    参数:
        rankings: 多路排名，每路是一个 chunk_id 列表（从最相关到最不相关）
        k: RRF 常数，默认 60（标准值）

    返回:
        [(chunk_id, 融合分)]，按分数从高到低
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
