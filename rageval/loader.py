"""Day 28：语料扫描器（只扫 .py/.md，可追溯）。"""

import hashlib
import json
from pathlib import Path

# 只允许这两种扩展名（为什么：MVP 只处理代码和文档，别的先不要）
ALLOWED_SUFFIXES = {".py", ".md"}
# 这些目录永远跳过（为什么：.git 是 git 内部数据、venv 是环境、__pycache__ 是缓存，都不是"语料"）
SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", ".idea"}


def content_hash(text: str) -> str:
    """内容哈希（为什么：文件被改一个字，哈希就变，能发现语料被篡改）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_corpus(root: Path) -> list[dict]:
    """扫描目录，返回记录列表。"""
    records = []
    for path in root.rglob("*"):  # rglob = 递归找所有文件
        if not path.is_file() or path.suffix not in ALLOWED_SUFFIXES:
            continue  # 不是文件，或扩展名不在白名单 → 跳过
        if any(part in SKIP_DIRS for part in path.parts):
            continue  # 路径里含有要跳过的目录 → 跳过
        content = path.read_text(encoding="utf-8")
        records.append({
            "file_path": str(path.relative_to(root)),   # 相对路径，便于定位
            "content": content,                          # 文件全文
            "language": "python" if path.suffix == ".py" else "markdown",
            "content_hash": content_hash(content),       # 内容指纹
        })
    return records


def build_manifest(corpus_dir: str, source_url: str, commit_sha: str, license_name: str) -> dict:
    """生成清单（为什么：一次把'语料从哪来、什么版本、多少个文件'全记下来）。"""
    records = scan_corpus(Path(corpus_dir))
    return {
        "source_url": source_url,      # 来源仓库地址
        "commit_sha": commit_sha,      # 代码版本指纹
        "license": license_name,       # 许可协议
        "file_count": len(records),    # 文件数
        "files": records,              # 全部记录
    }


if __name__ == "__main__":
    # 为什么用 evalhub_core 当语料：你自己的代码、有公共仓库、可追溯
    manifest = build_manifest(
        corpus_dir="D:/PycharmProjects/EvalHub-course/evalhub_core",
        source_url="https://github.com/xl819436-creator/EvalHub",
        commit_sha="d6d71436035b2ffa54b1031586a72a2b4d8278e3",
        license_name="MIT",
    )
    # 写文件（为什么用 ensure_ascii=False：保留中文，别变成 \uXXXX）
    Path("corpus_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"扫描完成：{manifest['file_count']} 个文件，已写入 corpus_manifest.json")