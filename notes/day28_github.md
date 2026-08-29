# Day 28 GitHub 任务记录（L3 语料固定，逐小步）

## 第 1 步：ChunkHound（只读 README，记定位）

- 仓库：<https://github.com/chunkhound/chunkhound>（官网 <https://chunkhound.ai>；课程线索为 FlagOpen 出品，GitHub 上以 chunkhound 为名的主要仓库为 chunkhound/chunkhound）
- 一句话定位：开源代码库智能（open-source codebase intelligence）——为 agent 和团队提供跨**当前代码、git 历史、技术网络调研**的**引用上下文（cited context）**。
- README 原文摘录：
  - "Local-first · Dozens of languages & file types · Cited answers · Git history research · Pinpoint web research"
  - "Your entire engineering context, deeply understood."
- 定位关键词（对应任务要求）：**cited context（引用上下文）** + **local-first（本地优先）**
- 与 RAGEval 的关系：ChunkHound 面向生产级"agent 引用真实代码上下文"，RAGEval 是教学 MVP，只做"扫描语料 + 内容哈希 + 余弦相似度"的最小可追溯链路；两者共同点都是**可追溯**（ChunkHound 用 cited answers，RAGEval 用 content_hash）。

## 第 2 步：Ragas（只看 README 前两段）

- 仓库：<https://github.com/explodinggradients/ragas>
- 一句记录：**Ragas 是评测 RAG 质量的库。**
- README 前两段核实（2026-08-29）：
  - tagline：*Supercharge Your LLM Application Evaluations 🚀*
  - 正文：*Objective metrics, intelligent test generation, and data-driven insights for LLM apps*
  - 正文：*Ragas is your ultimate toolkit for evaluating and optimizing Large Language Model (LLM) applications.*
- 与 RAGEval 的关系：Ragas 是成熟 RAG 评测框架（LLM-based + 传统指标、测试数据生成），RAGEval 先用 3 个手工向量演示余弦相似度，再接入 Embedding——从最小可复现链路起步，不做前端。

## 参考

- <https://github.com/chunkhound/chunkhound/blob/main/README.md>
- <https://github.com/explodinggradients/ragas/blob/main/README.md>
