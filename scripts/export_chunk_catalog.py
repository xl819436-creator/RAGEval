"""Day 33 辅助：导出语料分块后的完整 chunk 清单，供标注评测集时精确引用 chunk_id。

用法：
    D:\Annaconda\envs\evalhub-py311\python.exe scripts\export_chunk_catalog.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from rageval.chunkers import PythonASTChunker


def main() -> None:
    manifest = json.loads(Path("corpus_manifest.json").read_text(encoding="utf-8"))
    chunker = PythonASTChunker()
    lines = [f"# 语料：{manifest.get('source_url', '')} @ {manifest.get('commit_sha', '')}"]
    index = 0
    for record in manifest["files"]:
        for chunk in chunker.chunk(text=record["content"], path=record["file_path"]):
            index += 1
            chunk_id = f"{chunk.path}:{chunk.start_line}-{chunk.end_line}"
            preview = chunk.content.replace("\n", " ")[:70]
            lines.append(f"{index:3d}\t{chunk_id}\t[{chunk.symbol_name or ''}]\t{preview}")
    out = Path("experiments/chunk_catalog.txt")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"已导出 {index} 个 chunk 到 {out}")


if __name__ == "__main__":
    main()
