# Citation 契约（Day 32）

## 数据模型

| 字段 | 类型 | 含义 |
|---|---|---|
| file_path | str | 引用来源文件（语料相对路径） |
| symbol_name | str \| None | 符号名（AST 分块可得函数/类名） |
| line_range | (start, end) | 行号范围，1 起，可回原文定位 |
| quote | str | 原文摘录，用于核验 |

## 核验规则

- verify_citation：quote 必须出现在 file_lines[line_range] 内
- 引用指向的行必须真实存在该文本 → 防止编造出处

## 拒答规则

- 置信度 = 重排第一名候选的查询词覆盖率（0~1）
- confidence < refuse_threshold（默认 0.5）→ 拒答并记录原因
- 阈值写入配置快照（answer_pipeline.config）