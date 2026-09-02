# RAGEval 消融实验报告（Day 34）

- 评测集：`data/rag_evalset_v1.jsonl`（30 条；27 条可答参与指标，3 条 out-of-scope 用于拒答验证）
- RAGEval commit SHA（运行消融的代码快照，`git rev-parse HEAD`）：`9086c45edcfea5532f8e7a32115de10994da4a79`
- 语料来源 commit SHA（`corpus_manifest.json` 记录，同一 corpus 未改动）：EvalHub `d6d71436035b2ffa54b1031586a72a2b4d8278e3`
- 检索指标：Recall@5 / MRR / NDCG@5 / P95（ms），实现在 `rageval/retrieval_metrics.py`
- 重跑命令：`D:\Annaconda\envs\evalhub-py311\python.exe scripts\ablation_runner.py`（原始结果见 `raw_results/ablation_*.json`）

## 汇总表

| 组名 | 分块 | 检索 | 重排 | Recall@5 | MRR | NDCG@5 | P95(ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| ast_vector | AST | vector | 否 | 0.6111 | 0.3272 | 0.3979 | 5.49 |
| ast_bm25 | AST | bm25 | 否 | 0.6296 | 0.3543 | 0.4242 | 0.36 |
| ast_rrf | AST | rrf | 否 | 0.6111 | 0.3253 | 0.3969 | 5.99 |
| fixed_vector | Fixed | vector | 否 | 0.0 | 0.0 | 0.0 | 23.20 |
| fixed_bm25 | Fixed | bm25 | 否 | 0.0 | 0.0 | 0.0 | 0.49 |
| fixed_rrf | Fixed | rrf | 否 | 0.0 | 0.0 | 0.0 | 24.84 |
| ast_rrf_rerank | AST | rrf | 是 | 0.6111 | 0.3747 | 0.4339 | 5.97 |

（7 组 × 27 条可答问题；P95 = 单次检索延迟 95 分位，单位毫秒，由 runner 实测记录）

## 观察（如实，不虚构提升）

- **BM25 略优于 vector（词面匹配对代码符号有效）**：`ast_bm25`（Recall@5 0.6296 / MRR 0.3543 / NDCG@5 0.4242）全面高于 `ast_vector`（0.6111 / 0.3272 / 0.3979）——函数名、类名这类代码符号靠精确词面匹配（BM25）比词袋余弦更有效。
- **RRF + 重排使 MRR / NDCG 提升**：`ast_rrf_rerank`（MRR 0.3747 / NDCG@5 0.4339）高于 `ast_rrf`（0.3253 / 0.3969）；重排只改变排序不动召回，所以 Recall@5 保持 0.6111 不变、MRR/NDCG 上升，符合机制预期。
- **Fixed 分块全 0（失败原因如实记录）**：评测集的相关块按 **AST 行号**标注（如 `cost.py:17-45`），Fixed 按固定字符数切块、边界不同，**无法精确命中标注的块** → 三个检索器全部 0.0。这说明**评测集标注与分块策略耦合**：换分块策略必须重新标注评测集，否则指标无意义——这是 RAG 评测的已知难点，指标没提升就如实写失败原因，不假装提升。

## 失败案例分析（3 例）

评测集 30 条中 3 条为 out-of-scope（`answerable: false`、`relevant_chunk_ids: []`），用于验证"检索器对不可答问题不应给出有用命中"。用 vector 检索逐条查看：

- **e028「如何在 Kubernetes 上部署 EvalHub？」**：词袋分词器只保留 `[a-z0-9_]`，中文全被丢弃，只剩 `kubernetes` / `evalhub` 两个英文 token → 泛匹配到 `__init__.py:1-4`（项目简介含 "EvalHub"），score 0.316 的假阳性命中。Kubernetes 部署在语料中不存在，本应拒答。
- **e029「EvalHub 支持中文分词器配置吗？」**：同上只剩 `evalhub` 一个 token，命中同一个 `__init__.py:1-4`（0.316）。问题问"中文分词器配置"这一语料没有的能力，词袋既覆盖不到中文语义、也无法理解"是否支持"这类能力问句。
- **e030「这个项目用什么向量数据库做语义检索？」**：整句为中文抽象概念（向量数据库 / 语义检索），分词后 token 为空 → 查询向量全 0 → 所有 chunk 相似度 0.0，top1 退化为任意第一块 `async_deepseek.py:23-110`。语义问句没有字面关键词可匹配，词袋模型结构性失效。

**共性结论**：词袋向量对**中文问题**与**抽象语义问句**覆盖不到（分词器丢弃中文），是当前最小 MVP 的已知限制；正式系统应接入真实 Embedding（如 sentence-transformers），并在最高分低于阈值时拒答（衔接 Day 32 的拒答设计）。
