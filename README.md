# RAGEval

RAGEval 是一个从最小可复现链路学习 RAG（检索增强生成）与检索评测的 Python 项目：扫描小型代码仓库作为固定语料，做 **分块（Fixed/AST）→ 索引（词袋向量/BM25）→ 混合检索（RRF）→ 重排 → 引用标注 → 评测指标** 的完整链路，全部代码可复现、指标来自保存的原始结果（40 天学习路线 Day 28 起，MVP 不做前端）。

## 架构

```text
语料（EvalHub 仓库，corpus_manifest.json）
  → chunkers：FixedChunker / PythonASTChunker（块带路径 + 行号 + 符号名）
  → index：embeddings（词袋 TF）/ bm25_retriever / vector_index
  → 混合：rrf（结果融合）
  → reranker（重排）
  → citation（引用标注）→ answer_pipeline（检索→生成→评分）
  → retrieval_metrics（Recall@5 / MRR / NDCG@5 / P95）
  → 实验：scripts/ablation_runner.py → raw_results/ + reports/ablation.md
  → 服务：api/main.py（FastAPI /health + /rag/search）
```

| 模块 | 职责（对应 Day） |
|---|---|
| `rageval/loader.py` | 语料扫描：只收 `.py/.md`，跳过 `.git/venv/__pycache__/.idea`，算 SHA-256 content_hash（Day 28） |
| `rageval/embeddings.py` | 词袋向量 BagOfWords（零依赖 TF，可替换为真实 Embedding）（Day 28） |
| `rageval/cosine.py` | 余弦相似度（相同=1、垂直=0 的手工演示）（Day 28） |
| `rageval/chunkers.py` | FixedChunker（固定字符 + overlap）与 PythonASTChunker（按类/函数/异步函数切块，语法错误自动降级并记 fallback_reason）（Day 29） |
| `rageval/bm25_retriever.py` | BM25 词面检索（对代码符号名/类名精确匹配有效）（Day 30–31） |
| `rageval/vector_index.py` | 向量索引与 Top-K 检索（Day 30） |
| `rageval/rrf.py` | 混合检索结果融合（Day 31） |
| `rageval/reranker.py` | 重排（Day 32） |
| `rageval/citation.py` | 引用标注：只回答语料内能找到依据的内容（Day 32） |
| `rageval/answer_pipeline.py` | 检索 → 生成 → 评分流水线（Day 33） |
| `rageval/retrieval_metrics.py` | Recall@5 / MRR / NDCG@5 / P95 指标（Day 33） |
| `api/main.py` | FastAPI：`/health` + `/rag/search`（启动时加载语料建索引）（Day 33+） |

## 功能

- 扫描语料并生成带来源 URL / commit SHA / 许可 / 文件哈希的清单（`corpus_manifest.json`）
- 两种分块器可切换：固定长度分块与按 Python 语法结构的 AST 分块（块含路径、行号、符号名）
- 语法错误文件自动降级为固定分块并记录 `fallback_reason`
- 两种检索：BM25 词面检索与词袋向量 Top-K 检索；RRF 混合融合；重排
- 引用标注：检索不到依据的问题拒绝作答（答不了就不答）
- RAG 检索评测指标：Recall@5 / MRR / NDCG@5 / P95 延迟，实测记录
- 最小 HTTP 服务：`/health` 与 `/rag/search`

## Quick Start

```powershell
git clone https://github.com/xl819436-creator/RAGEval.git
cd RAGEval
conda create -n rageval-py311 python=3.11 -y
conda activate rageval-py311
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
```

跑通消融实验（7 组，约 1 分钟内出结果）：

```powershell
python scripts/ablation_runner.py
# 终端输出汇总；原始结果 raw_results/ablation_*.json，完整报告 reports/ablation.md
```

## 测试

```powershell
python -m pytest -q
```

本机实测（2026-08-29，Python 3.11.15）：**36 passed**，覆盖 loader、chunkers（含降级/行号/符号完整率）、embeddings、余弦、BM25/向量检索、RRF、rerank、citation、answer_pipeline、retrieval_metrics 与 API。

## 实验结果

消融实验（Day 34，`data/rag_evalset_v1.jsonl`，30 条中 27 条可答参与指标；评测集与语料 commit 见 `reports/ablation.md`）：

| 组名 | 分块 | 检索 | 重排 | Recall@5 | MRR | NDCG@5 | P95(ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| ast_vector | AST | vector | 否 | 0.6111 | 0.3272 | 0.3979 | 5.49 |
| ast_bm25 | AST | bm25 | 否 | **0.6296** | **0.3543** | 0.4242 | 0.36 |
| ast_rrf | AST | rrf | 否 | 0.6111 | 0.3253 | 0.3969 | 5.99 |
| fixed_vector | Fixed | vector | 否 | 0.0 | 0.0 | 0.0 | 23.20 |
| fixed_bm25 | Fixed | bm25 | 否 | 0.0 | 0.0 | 0.0 | 0.49 |
| fixed_rrf | Fixed | rrf | 否 | 0.0 | 0.0 | 0.0 | 24.84 |
| ast_rrf_rerank | AST | rrf | 是 | 0.6111 | 0.3747 | **0.4339** | 5.97 |

原始结果：`reports/ablation_*.json`（完整分析见 `reports/ablation.md`，RAGEval commit `9086c45`，语料 EvalHub commit `d6d7143`）。

## 失败案例

- **Fixed 分块三组指标全 0（如实记录，不假装提升）**：评测集的相关块按 **AST 行号**标注（如 `cost.py:17-45`），而 Fixed 分块按固定字符切、边界不同 → 无法精确命中标注块 → `fixed_vector/bm25/rrf` 的 Recall@5/MRR/NDCG 全部 0.0。这暴露了 RAG 评测的已知难点：**评测集标注与分块策略耦合**——换分块策略必须重新标注评测集，否则指标无意义。
- **词袋向量对中文/抽象问句失效**：评测集中 3 条 out-of-scope 问题全部被词袋误命中（如"如何在 Kubernetes 部署 EvalHub"分词后只剩 `kubernetes/evalhub` 两个 token → 泛匹配到 `__init__.py` 假阳性命中）。词袋分词只保留 `[a-z0-9_]`，中文语义覆盖不到，正式场景应换真实 Embedding 并对低分命中拒答。

## 已知限制

- **词袋向量（BagOfWords）**：分词只保留 `[a-z0-9_]`，中文与标点被丢弃，纯中文或抽象语义问句检索会失效（查询向量为空 → 全 0 分或假阳性命中）；教学 MVP 用它演示完整链路，正式场景应换真实 Embedding 模型
- **MockReranker**：重排器为规则/占位实现，只演示"重排改变排序"这一机制，不代表真实模型重排效果
- **Fixed 分块与评测标注耦合**：评测集按 AST 行号标注相关块，Fixed 分块边界不同导致无法精确命中（消融中 Fixed 三组指标全 0）；换分块策略时必须重新标注评测集

## 项目结构

```text
RAGEval/
├── rageval/            # 核心库（见上方架构表）
├── api/main.py         # FastAPI：/health + /rag/search
├── scripts/            # ablation_runner.py 等实验脚本
├── data/               # rag_evalset_v1.jsonl（30 条评测集）
├── raw_results/        # 消融原始输出（重跑生成）
├── reports/            # ablation.md + 7 组 ablation_*.json
├── docs/               # chunking_experiment.md、citation_contract.md 等
├── corpus_manifest.json  # 语料清单（来源、commit SHA、许可、文件与哈希）
├── notes/              # 学习记录
└── README.md
```

## 语料来源

- 仓库：<https://github.com/xl819436-creator/EvalHub>
- commit SHA：`d6d71436035b2ffa54b1031586a72a2b4d8278e3`
- 许可：MIT
- 文件数：23（完整清单见 `corpus_manifest.json`）
