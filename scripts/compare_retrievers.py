"""Day 31：三路检索对比（向量 / BM25 / RRF），输出 Top-10 与命中判断到 CSV。

用法：
    D:\Annaconda\envs\evalhub-py311\python.exe scripts\compare_retrievers.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import csv
import json

from rageval.bm25_retriever import BM25Retriever
from rageval.chunkers import PythonASTChunker
from rageval.embeddings import BagOfWords
from rageval.rrf import reciprocal_rank_fusion
from rageval.vector_index import VectorIndex

TOP_K = 10


def load_chunks() -> list[dict]:
    """读语料 -> 分块 -> 转成统一协议 dict。"""
    manifest = json.loads(Path("corpus_manifest.json").read_text(encoding="utf-8"))
    chunker = PythonASTChunker()
    chunks = []
    for record in manifest["files"]:
        for chunk in chunker.chunk(text=record["content"], path=record["file_path"]):
            chunks.append({
                "chunk_id": f"{chunk.path}:{chunk.start_line}-{chunk.end_line}",
                "file_path": chunk.path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.content,
            })
    return chunks


def hit_rank(hits, expected_file: str) -> int:
    """返回预期文件第一次出现在结果里的排名（1 起）；没命中返回 0。"""
    for idx, hit in enumerate(hits, start=1):
        if hit.file_path == expected_file:
            return idx
    return 0


def main() -> None:
    chunks = load_chunks()

    # 三路检索器（为什么三路用同一份 chunks：保证可比）
    bow = BagOfWords()
    bow.fit([c["text"] for c in chunks])
    vector = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    vector.build(chunks)

    bm25 = BM25Retriever()
    bm25.build(chunks)

    queries = [
        json.loads(line)
        for line in Path("data/retrieval_queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = []
    summary: dict[str, list[int]] = {"vector": [], "bm25": [], "rrf": []}

    for q in queries:
        v_hits = vector.vector_search(q["query"], top_k=TOP_K)
        b_hits = bm25.search(q["query"], top_k=TOP_K)
        # RRF：用两路排名融合（rankings = 各路的 chunk_id 字符串列表）
        v_ids = [h.chunk_id for h in v_hits]
        b_ids = [h.chunk_id for h in b_hits]
        fused = reciprocal_rank_fusion([v_ids, b_ids])
        rrf_ids = [cid for cid, _ in fused]
        by_id = {h.chunk_id: h for h in v_hits + b_hits}
        rrf_hits = [by_id[cid] for cid in rrf_ids if cid in by_id][:TOP_K]

        for name, hits in (("vector", v_hits), ("bm25", b_hits), ("rrf", rrf_hits[:TOP_K])):
            rank = hit_rank(hits, q["expected_file"])
            summary[name].append(rank)
            top = hits[0] if hits else None
            rows.append({
                "query_id": q["id"], "query": q["query"], "category": q["category"],
                "retriever": name, "hit_rank": rank, "hit": 1 if rank > 0 else 0,
                "top1_file": top.file_path if top else "",
                "top1_score": top.score if top else "",
            })

    out = Path("experiments/retrieval_compare.csv")
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 汇总：每路的命中率@10 和平均排名（0 表示没命中，不计入平均排名）
    print("=== 三路对比汇总（10 个问题，Top-10 命中率）===")
    for name, ranks in summary.items():
        hits = sum(1 for r in ranks if r > 0)
        avg_rank = sum(r for r in ranks if r > 0) / hits if hits else 0
        print(f"{name:>6}: 命中 {hits}/10, 平均命中排名 {avg_rank:.2f}")
    print(f"\n明细已写入 {out}")
    for row in rows:
        if row["retriever"] == "vector":
            print(f"[{row['query_id']}] {row['query']} -> vector rank={row['hit_rank']}")


if __name__ == "__main__":
    main()
