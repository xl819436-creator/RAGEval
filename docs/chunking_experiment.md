# Day 29 分块实验：FixedChunker vs PythonASTChunker

- 实验日期：2026-08-29 ｜ 样本：rageval/chunkers.py（3599 字符，8 个符号）
- 参数：chunk_size=200, overlap=20

| 分块器 | 块数 | 平均长度 | 符号完整率 |
|---|---:|---:|---:|
| FixedChunker | 20 | 199 字符 | 12% |
| PythonASTChunker | 8 | 722 字符 | 100% |

结论：固定分块按字符硬切，8 个符号只有 12% 完整；AST 分块按类/函数边界切，
完整率 100%。语义边界分块更适合作为 RAG 检索单元（块=完整函数，命中即拿到完整上下文）。