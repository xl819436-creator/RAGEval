# RAGEval

RAGEval 是一个从最小可复现链路学习 RAG（检索增强生成）评测的 Python 项目：扫描小型代码仓库作为语料，用词袋向量与余弦相似度演示"相似度检索"的核心概念（40 天学习路线 Day 28 起，MVP 只处理 .py/.md，不做前端）。

## 当前能力

- **语料扫描**：递归扫描指定目录，只收录 `.py` / `.md` 文件，跳过 `.git`、`venv`、`__pycache__`、`.idea`、`node_modules`
- **内容指纹**：为每个文件计算 SHA-256 `content_hash`，文件内容改动一个字哈希即变，可追溯语料是否被篡改
- **语料清单**：`corpus_manifest.json` 记录来源仓库 URL、commit SHA、许可协议、文件总数与全部文件内容（含相对路径、语言、哈希）
- **文本向量**：`BagOfWords` 词袋向量器（零依赖 TF 向量，`embedding.py`），将来可无缝替换为真实 Embedding 模型
- **余弦相似度**：`cosine_similarity`（`cosine.py`），用 3 个手工向量演示——相同向量相似度为 1，垂直向量为 0

## 语料来源

- 仓库：<https://github.com/xl819436-creator/EvalHub>
- commit SHA：`d6d71436035b2ffa54b1031586a72a2b4d8278e3`
- 许可：MIT
- 文件数：23（完整清单见 `corpus_manifest.json`）

## 如何运行

在仓库根目录、Python 3.11+ 环境执行：

```powershell
# 1. 重新扫描语料并生成 corpus_manifest.json
#    （注意：先检查 rageval/loader.py 末尾的 corpus_dir 与 commit_sha 是否最新）
python rageval/loader.py

# 2. 手工向量余弦相似度演示（预期输出：a·a = 1.0，a·c = 0.0）
python rageval/cosine.py

# 3. 词袋向量：把一段文本变成向量
python -c "from rageval.embedding import BagOfWords; b = BagOfWords(); b.fit(['rag eval']); print(b.embed('rag eval'))"
```

## 项目结构

```text
RAGEval/
├── rageval/
│   ├── __init__.py
│   ├── loader.py       # 语料扫描 + content_hash + manifest 生成
│   ├── embedding.py    # 词袋向量（零依赖）
│   └── cosine.py       # 余弦相似度（手工向量演示）
├── corpus_manifest.json  # 语料清单（来源、commit SHA、许可、文件与哈希）
├── notes/                # 学习记录（day28.md、day28_github.md）
└── README.md
```

## 边界与后续

- 当前向量为词袋 TF，不包含语义；后续接入真实 Embedding 时只需替换 `embed(text)` 的实现
- 语料固定为 EvalHub 仓库（L3 语料固定），保证可追溯、可复现
