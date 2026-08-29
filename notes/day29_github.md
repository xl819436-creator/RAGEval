# Day 29 GitHub 任务记录（L3 定位相关实现：分块 / 解析 / 符号模块）

调研日期：2026-08-29
仓库：<https://github.com/chunkhound/chunkhound>（main 分支，约 1421 stars，定位 "Your entire engineering context, deeply understood"）

## 第 6 步：对照 ChunkHound 理解成熟项目里分块 / 解析 / 符号模块怎么组织

### 1. 调研方法

- 在仓库搜索框分别搜 `chunk`、`parser`、`symbol` 三个词；
- 只看**文件 / 模块名**，画出模块关系，不逐行读代码。

### 2. ChunkHound 模块地图（只列文件 / 模块名）

```
chunkhound/
├── parsers/                      # 解析体系（核心）
│   ├── parser_factory.py         # 按语言选择解析器的工厂
│   ├── universal_parser.py       # 统一解析入口：cAST（Code AST）算法
│   ├── universal_engine.py       # TreeSitterEngine + ConceptExtractor 组合
│   ├── chunk_splitter.py         # 分块器（split-then-merge）
│   ├── concept_extractor.py      # 语义概念抽取
│   ├── mappings/                 # 每种语言一个映射模块
│   │   ├── base.py               # 语言映射基类（BaseMapping）
│   │   ├── python.py / javascript.py / go.py / rust.py / java.py / cpp.py …
│   │   └── （共约 40 种语言映射文件，如 bash/c/css/dart/elixir/hcl/kotlin/…）
│   ├── svelte_parser.py / vue_parser.py / rapid_yaml_parser.py / makefile_parser.py
│   ├── twincat/                  # 专属语言解析器（含 .lark 语法文件）
│   └── embedded_sql_detector.py  # 嵌入式 SQL 检测
├── core/
│   ├── models/chunk.py           # 跨语言统一的 Chunk 数据模型
│   └── utils/chunk_utils.py      # 分块工具函数
├── interfaces/language_parser.py # 解析器协议 / 接口
├── core/detection/language_detector.py  # 语言识别
└── code_mapper/                  # 基于 LLM 的代码映射（HyDE 等，生产功能）
```

- **symbol 相关**：ChunkHound **没有独立的 `symbols/` 模块**；符号（函数 / 类等）由各语言 mapping 用 tree-sitter query 提取，符号相关逻辑在测试中验证（`tests/unit/test_symbol_suffix_stripping.py`、`tests/services/test_unified_search_symbol_extraction.py`）。

### 3. 与我的 `rageval/chunkers.py` 对应关系

| 维度 | ChunkHound（生产） | 我的 `rageval/chunkers.py`（教学） |
|---|---|---|
| 定位 | 生产级：工程上下文语义理解、索引、引用 | 教学级：最小可复现链路，演示分块概念 |
| 语言范围 | 约 40 种语言（tree-sitter 统一） | 仅 Python |
| AST 来源 | **tree-sitter 第三方库** + 每语言 query | **标准库 `ast`**（`ast.parse` / `ast.walk` / `ast.get_source_segment`） |
| 分块策略 | cAST split-then-merge + 概念抽取 | `FixedChunker`（定长 + overlap）+ `PythonASTChunker`（按类 / 函数切） |
| 块数据模型 | `core/models/chunk.py`（跨语言统一） | `Chunk` dataclass（path / start_line / end_line / content / symbol_name / chunk_type / fallback_reason） |
| 符号处理 | mapping 层 tree-sitter query 提取 | `symbol_name` 字段 + `symbol_completeness()` 量化完整率 |
| 容错 | 生产级诊断（batch_metrics / perf_analyzer 等） | 语法错误或无符号时降级为 fixed，记录 `fallback_reason`，绝不崩溃 |
| 组织方式 | `parsers/mappings/` 每语言一模块 + 工厂 | 一个文件两个类，直接实例化 |

**模块路径对照（ChunkHound → RAGEval）**：

- `chunkhound/parsers/mappings/python.py` → `rageval/chunkers.py` 的 `PythonASTChunker`（功能对应：提取类 / 函数 / 异步函数）
- `chunkhound/parsers/chunk_splitter.py` → `FixedChunker`
- `chunkhound/core/models/chunk.py` → `Chunk` dataclass
- `chunkhound/core/utils/chunk_utils.py` → `symbol_completeness()`
- `chunkhound/parsers/parser_factory.py` → 教学版暂无（类少，直接实例化即可）

### 4. 结论

- ChunkHound 是**生产项目**：为支持 40+ 语言，选择 **tree-sitter**（成熟第三方解析库）+ 每语言 query，**没有手写词法 / 语法解析器**；
- RAGEval 是**教学项目**：只处理 Python，**标准库 `ast` 完全够用**，代码可读性好、零依赖；
- **结论：AST API 以标准库 `ast` 为准，不自己造轮子** —— Python 场景用 stdlib `ast`；将来跨语言再考虑 tree-sitter，同样是"用现成的轮子"。两个项目都没有、也不应该手写解析器。

## 参考

- <https://github.com/chunkhound/chunkhound>
- <https://github.com/chunkhound/chunkhound/tree/main/chunkhound/parsers>
- <https://github.com/chunkhound/chunkhound/blob/main/chunkhound/parsers/universal_parser.py>
- <https://github.com/chunkhound/chunkhound/blob/main/chunkhound/parsers/mappings/python.py>
- <https://github.com/chunkhound/chunkhound/blob/main/chunkhound/core/models/chunk.py>
