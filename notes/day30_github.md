# Day 30 GitHub 任务（ChunkHound 对照）

- ChunkHound 的检索输出概念 ≈ 我的 SearchHit（chunk_id / file_path / line_range / score）
- 我只实现最小接口（vector_search(query, top_k) -> SearchHit[]），不复制其全系统
- demo 结果可追溯：每个命中都带原始文件路径和行号