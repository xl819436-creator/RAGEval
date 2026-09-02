"""Day 33：对 30 条评测集跑检索器，输出 Recall@5/MRR/NDCG@5/P95 与手算核对数据。

用法：
    D:\Annaconda\envs\evalhub-py311\python.exe scripts\evaluate_evalset.py
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from rageval.bm25_retriever import BM25Retriever
from rageval.chunkers import PythonASTChunker
from rageval.embeddings import BagOfWords
from rageval.retrieval_metrics import mrr, ndcg_at_k, p95_latency, recall_at_k
from rageval.vector_index import VectorIndex


def load_chunks():
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


def main() -> None:
    chunks = load_chunks()
    bow = BagOfWords()
    bow.fit([c["text"] for c in chunks])
    vector = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    vector.build(chunks)

    evalset = [
        json.loads(line)
        for line in Path("data/rag_evalset_v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    answerable = [q for q in evalset if q["answerable"]]
    unanswerable = [q for q in evalset if not q["answerable"]]

    query_results = []
    latencies = []
    manual_rows = []  # 手算核对用的前 5 条明细

    for q in answerable:
        relevant = set(q["relevant_chunk_ids"])
        start = time.perf_counter()
        hits = vector.vector_search(q["question"], top_k=10)
        latencies.append((time.perf_counter() - start) * 1000)
        ranked = [h.chunk_id for h in hits]
        query_results.append((ranked, relevant))
        if len(manual_rows) < 5:  # 记录前 5 条做手算核对
            manual_rows.append({
                "id": q["id"], "question": q["question"],
                "relevant": sorted(relevant), "ranked_top5": ranked[:5],
                "first_hit_rank": next((i + 1 for i, c in enumerate(ranked) if c in relevant), 0),
            })

    print(f"评测集：共 {len(evalset)} 条，可答 {len(answerable)}，无答案 {len(unanswerable)}")
    r5 = sum(recall_at_k(r, rel, 5) for r, rel in query_results) / len(query_results)
    n5 = sum(ndcg_at_k(r, rel, 5) for r, rel in query_results) / len(query_results)
    print(f"Recall@5 = {r5:.4f}")
    print(f"MRR      = {mrr(query_results):.4f}")
    print(f"NDCG@5   = {n5:.4f}")
    print(f"P95 延迟 = {p95_latency(latencies):.2f} ms（{len(latencies)} 次查询）")

    print("\n=== 前 5 条手算核对明细 ===")
    for row in manual_rows:
        rr = row["first_hit_rank"]
        print(f"[{row['id']}] {row['question'][:30]}")
        print(f"   相关块: {row['relevant']}")
        print(f"   Top5  : {row['ranked_top5']}")
        print(f"   首个命中排名: {rr}  → reciprocal rank = {1/rr if rr else 0:.4f}")


if __name__ == "__main__":
    main()
