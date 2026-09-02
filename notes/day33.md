# Day 33 记录

## 实战题 1：相关块在第 3 位时的 reciprocal rank
- 手算：1/3 ≈ 0.3333（测试 test_reciprocal_rank_at_third_position 已验证）

## 实战题 2：无答案问题不标相关块
- e028-e030 的 relevant_chunk_ids 为空，answerable=false
- 无答案问题不参与检索指标，单独计数（3 条）

## 实战题 3：简单问题 vs 真实问题
- 简单问题：问题里直接含函数名（如 e002 "load_jsonl 在哪"）
- 真实问题：需要理解语义（如 e007 指数退避、e014 map_deepseek_response）
- 评测集 30 条中两者都有，避免只测"名字检索"