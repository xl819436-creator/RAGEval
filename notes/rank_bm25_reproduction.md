#①官方库装不上（清华源无此包）→ 自己实现 BM25Okapi；
#②官方库分词用词干化，我沿用词袋分词（与向量检索一致，保证公平）；
#③接口对齐（我实现 build(chunks) + search(query, top_k)，与 VectorIndex 同协议）；