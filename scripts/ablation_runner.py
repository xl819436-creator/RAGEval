"""Day 34：消融实验——分块 × 检索 × 重排，每次只改一个变量。

用法（在 RAGEval 项目根目录）：
    D:\Annaconda\envs\evalhub-py311\python.exe scripts\ablation_runner.py

输出：raw_results/ablation_*.json（每组的原始结果）+ 终端汇总。
实验固定使用 data/rag_evalset_v1.jsonl（同一评测集），只比较可答问题。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径（直接运行 scripts\*.py 时必需）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
import json
import time
from pathlib import Path

from rageval.bm25_retriever import BM25Retriever, tokenize
from rageval.chunkers import FixedChunker, PythonASTChunker
from rageval.embeddings import BagOfWords
from rageval.retrieval_metrics import mrr, ndcg_at_k, p95_latency, recall_at_k
from rageval.rrf import reciprocal_rank_fusion
from rageval.vector_index import VectorIndex

TOP_K = 10   # 初召回数量
EVAL_K = 5   # 指标只看前 K


def load_chunks(chunker_cls) -> tuple[list[dict], dict[str, dict]]:
    """用指定分块器把语料分块，返回 chunks 与 chunks_by_id。"""
    manifest = json.loads(Path("corpus_manifest.json").read_text(encoding="utf-8"))
    chunker = chunker_cls()
    chunks = []
    for record in manifest["files"]:
        for c in chunker.chunk(text=record["content"], path=record["file_path"]):
            chunks.append({
                "chunk_id": f"{c.path}:{c.start_line}-{c.end_line}",
                "file_path": c.path,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "text": c.content,
            })
    by_id = {c["chunk_id"]: c for c in chunks}
    return chunks, by_id


def make_retrievers(chunks):
    """两个基础检索器（vector / bm25）；RRF 由两者融合生成。"""
    bow = BagOfWords()
    bow.fit([c["text"] for c in chunks])
    vector = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    vector.build(chunks)
    bm25 = BM25Retriever()
    bm25.build(chunks)
    return vector, bm25


def retrieve_ranked_ids(query: str, key: str, vector, bm25) -> list[str]:
    """按检索器返回 ranked chunk_id 列表（Top-10）。"""
    if key == "vector":
        return [h.chunk_id for h in vector.vector_search(query, top_k=TOP_K)]
    if key == "bm25":
        return [h.chunk_id for h in bm25.search(query, top_k=TOP_K)]
    v = [h.chunk_id for h in vector.vector_search(query, top_k=TOP_K)]
    b = [h.chunk_id for h in bm25.search(query, top_k=TOP_K)]
    return [cid for cid, _ in reciprocal_rank_fusion([v, b])]


def rerank_by_coverage(query: str, ranked_ids: list[str], by_id: dict[str, dict]) -> list[str]:
    """模拟 Reranker：按'查询词在块文本里的覆盖率'重排（与 Day 32 MockReranker 同信号）。"""
    query_tokens = set(tokenize(query))

    def coverage(chunk_id: str) -> float:
        if not query_tokens:
            return 0.0
        text_tokens = set(tokenize(by_id[chunk_id]["text"]))
        return len(query_tokens & text_tokens) / len(query_tokens)

    return sorted([c for c in ranked_ids if c in by_id], key=coverage, reverse=True)


def main() -> None:
    queries = [
        json.loads(line)
        for line in Path("data/rag_evalset_v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    answerable = [q for q in queries if q["answerable"]]

    # 实验组：每次只改一个变量（分块器 / 检索器 / 是否重排）
    experiments = [
        ("ast_vector", PythonASTChunker, "vector", False),
        ("ast_bm25", PythonASTChunker, "bm25", False),
        ("ast_rrf", PythonASTChunker, "rrf", False),
        ("fixed_vector", FixedChunker, "vector", False),
        ("fixed_bm25", FixedChunker, "bm25", False),
        ("fixed_rrf", FixedChunker, "rrf", False),
        ("ast_rrf_rerank", PythonASTChunker, "rrf", True),
    ]

    summary_rows = []
    Path("raw_results").mkdir(exist_ok=True)

    for name, chunker_cls, retriever_key, use_rerank in experiments:
        chunks, by_id = load_chunks(chunker_cls)
        vector, bm25 = make_retrievers(chunks)

        latencies = []
        rows = []
        for q in answerable:
            relevant = set(q["relevant_chunk_ids"])
            start = time.perf_counter()
            ranked = retrieve_ranked_ids(q["question"], retriever_key, vector, bm25)
            if use_rerank:
                ranked = rerank_by_coverage(q["question"], ranked, by_id)
            latencies.append((time.perf_counter() - start) * 1000)
            rows.append({"id": q["id"], "ranked": ranked[:EVAL_K], "relevant": sorted(relevant)})

        r5 = sum(recall_at_k(r["ranked"], set(r["relevant"]), EVAL_K) for r in rows) / len(rows)
        mr = mrr([(r["ranked"], set(r["relevant"])) for r in rows])
        n5 = sum(ndcg_at_k(r["ranked"], set(r["relevant"]), EVAL_K) for r in rows) / len(rows)
        p95 = p95_latency(latencies)
        result = {
            "name": name,
            "chunker": chunker_cls.__name__,
            "retriever": retriever_key,
            "rerank": use_rerank,
            "recall_at_5": round(r5, 4),
            "mrr": round(mr, 4),
            "ndcg_at_5": round(n5, 4),
            "p95_ms": round(p95, 2),
            "chunk_count": len(chunks),
            "evaluated_queries": len(rows),
        }
        (Path("raw_results") / f"ablation_{name}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        summary_rows.append(result)

    print("=== 消融实验汇总（同一评测集，仅可答问题）===")
    print(f"{'name':<16}{'chunker':<10}{'retriever':<9}{'rerank':<7}"
          f"{'Recall@5':<9}{'MRR':<8}{'NDCG@5':<8}{'P95ms':<8}{'chunks'}")
    for r in summary_rows:
        print(f"{r['name']:<16}{r['chunker']:<10}{r['retriever']:<9}{str(r['rerank']):<7}"
              f"{r['recall_at_5']:<9}{r['mrr']:<8}{r['ndcg_at_5']:<8}{r['p95_ms']:<8}{r['chunk_count']}")
    print("\n原始结果已写入 raw_results/ablation_*.json")


if __name__ == "__main__":
    main()