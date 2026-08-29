"""Day 30 实战题 3：比较 top_k=3/5/10 的命中数与耗时。"""

import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径（直接运行 scripts\*.py 时必需）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import time

from rageval.chunkers import PythonASTChunker
from rageval.embeddings import BagOfWords
from rageval.vector_index import VectorIndex

def main() -> None:
    # 读语料（Day 28 的清单）
    manifest = json.loads(Path("corpus_manifest.json").read_text(encoding="utf-8"))
    # 分块（Day 29 的 AST 分块器）
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
    # 向量化 + 建索引
    bow = BagOfWords()
    bow.fit([c["text"] for c in chunks])
    index = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
    index.build(chunks)

    # 分别用 top_k=3/5/10 检索，记录命中数和耗时
    for k in (3, 5, 10):
        start = time.perf_counter()
        hits = index.vector_search("load_jsonl", top_k=k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"top_k={k} -> {len(hits)} hits, {elapsed_ms:.2f} ms")


if __name__ == "__main__":
    main()