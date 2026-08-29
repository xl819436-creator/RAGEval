# Day 30 记录

## 实战题 1（top_k 超限不报错）
- 测试 test_top_k_larger_than_index_does_not_error 通过

## 实战题 2（空查询被拒绝）
- 测试 test_empty_query_rejected 通过（抛 ValueError: 查询不能为空）

## 实战题 3（Top-K=3/5/10 命中与耗时，实测）
- top_k=3 -> 3 hits, ~5.4 ms
- top_k=5 -> 5 hits, ~5.5 ms
- top_k=10 -> 10 hits, ~5.2 ms
- 结论：chunk 只有 117 个，暴力检索耗时差别很小；语料变大后差距才明显