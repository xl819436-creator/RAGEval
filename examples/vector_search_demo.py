"""Day 30：向量检索 Demo——从语料到 10 个问题的完整链路。"""

import json
import sys
from pathlib import Path

# 让脚本无论从哪个目录运行，都能 import 到项目根目录下的 rageval 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rageval.chunkers import PythonASTChunker
from rageval.embeddings import BagOfWords
from rageval.vector_index import VectorIndex


def main() -> None:
    # 1. 读语料（Day 28 生成的清单）
    manifest = json.loads(Path("corpus_manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]

    # 2. 分块（Day 29 的 AST 分块器；chunk(text, path)，块内记录可追溯路径和行号）
    chunker = PythonASTChunker()
    chunks = []
    for record in files:
        for chunk in chunker.chunk(text=record["content"], path=record["file_path"]):
            chunks.append({
                "chunk_id": f"{chunk.path}:{chunk.start_line}-{chunk.end_line}",
                "file_path": chunk.path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.content,
            })
    print(f"共 {len(chunks)} 个 chunk")

    # 3. 向量化 + 建索引（Day 28 词袋向量 + Day 30 索引）
    bow = BagOfWords()
    bow.fit([c["text"] for c in chunks])
    index = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    index.build(chunks)
    print("索引 manifest:", index.manifest())

    # 4. 10 个手工问题逐个检索（manual_queries.jsonl 是 JSONL：每行一个对象）
    lines = Path("data/manual_queries.jsonl").read_text(encoding="utf-8").splitlines()
    queries = [json.loads(line) for line in lines if line.strip()]
    for q in queries:
        hits = index.vector_search(q["query"], top_k=5)
        print(f"\n[{q['id']}] {q['query']}")
        for hit in hits:
            print(f"  {hit.score:.3f}  {hit.file_path}:{hit.line_range[0]}-{hit.line_range[1]}  ({hit.chunk_id})")


if __name__ == "__main__":
    main()
