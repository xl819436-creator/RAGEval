"""Day 32：检索→重排→带引用答案→低置信度拒答 的完整管道。

流程：初召回 Top-20（向量）→ MockReranker 重排取 Top-5 → 生成带引用答案 →
若置信度低于 refuse_threshold 则拒答并记录原因。
置信度 = 重排后第一名候选的覆盖率（0~1）。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rageval.chunkers import PythonASTChunker
from rageval.citation import Citation, verify_citation
from rageval.embeddings import BagOfWords
from rageval.reranker import Candidate, MockReranker
from rageval.vector_index import VectorIndex

RETRIEVE_TOP_K = 20   # 初召回 20
RERANK_TOP_K = 5      # 重排后取 5


@dataclass
class Refusal:
    """拒答结果：说明为什么拒绝回答。"""

    reason: str


@dataclass
class CitedAnswer:
    """可答结果：答案内容 + 引用列表 + 置信度。"""

    content: str
    citations: list[Citation]
    confidence: float


@dataclass
class AnswerResponse:
    """管道统一输出：要么可答（含引用），要么拒答。"""

    refused: bool
    answer: Optional[CitedAnswer] = None
    refusal: Optional[Refusal] = None
    config: dict = field(default_factory=dict)  # 配置快照（含阈值，验收用）


class RAGAnswerPipeline:
    """把语料建成索引，对问题走完整 RAG 管道。"""

    def __init__(self, refuse_threshold: float = 0.5):
        # 阈值写入配置快照（验收：阈值写入配置快照）
        self.config = {
            "retrieve_top_k": RETRIEVE_TOP_K,
            "rerank_top_k": RERANK_TOP_K,
            "refuse_threshold": refuse_threshold,
            "reranker": "mock",
        }
        self._files_by_path: dict[str, list[str]] = {}
        self._chunks_by_id: dict[str, dict] = {}
        self._vector: VectorIndex | None = None
        self._reranker = MockReranker()

    def build_from_manifest(self, manifest_path: str = "corpus_manifest.json") -> None:
        """加载语料清单，分块并建索引。"""
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        chunker = PythonASTChunker()
        chunks = []
        for record in manifest["files"]:
            self._files_by_path[record["file_path"]] = record["content"].splitlines()
            for chunk in chunker.chunk(text=record["content"], path=record["file_path"]):
                chunk_dict = {
                    "chunk_id": f"{chunk.path}:{chunk.start_line}-{chunk.end_line}",
                    "file_path": chunk.path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "text": chunk.content,
                    "symbol_name": chunk.symbol_name,
                }
                chunks.append(chunk_dict)
                self._chunks_by_id[chunk_dict["chunk_id"]] = chunk_dict
        bow = BagOfWords()
        bow.fit([c["text"] for c in chunks])
        self._vector = VectorIndex(embedding_model="bag-of-words-tf", embed_fn=bow.embed)
        self._vector.build(chunks)

    def answer(self, query: str) -> AnswerResponse:
        """完整管道：检索 → 重排 → 引用答案 / 拒答。"""
        if self._vector is None:
            raise RuntimeError("请先调用 build_from_manifest 建立索引")
        # 1) 初召回 Top-20
        hits = self._vector.vector_search(query, top_k=RETRIEVE_TOP_K)
        # 2) 组装候选（补文本与符号名）
        candidates = [
            Candidate(
                hit=hit,
                text=self._chunks_by_id[hit.chunk_id]["text"],
                symbol_name=self._chunks_by_id[hit.chunk_id].get("symbol_name"),
            )
            for hit in hits
        ]
        # 3) 重排取 Top-5
        scored = self._reranker.rerank(query, candidates)[:RERANK_TOP_K]
        if not scored:
            return AnswerResponse(
                refused=True,
                refusal=Refusal(reason="语料中没有可用的候选块"),
                config=self.config,
            )
        top = scored[0]
        confidence = top.rerank_score
        # 4) 低置信度拒答
        if confidence < self.config["refuse_threshold"]:
            return AnswerResponse(
                refused=True,
                refusal=Refusal(
                    reason=f"置信度 {confidence:.3f} 低于阈值 {self.config['refuse_threshold']}，"
                           f"疑似语料库外问题，拒绝回答"
                ),
                config=self.config,
            )
        # 5) 生成带引用答案（模板答案，MVP 不用 LLM）
        citations = []
        parts = []
        for item in scored:
            c = item.candidate
            quote = c.text.strip()[:60]
            citations.append(Citation(
                file_path=c.hit.file_path,
                symbol_name=c.symbol_name,
                line_range=(c.hit.line_range[0], c.hit.line_range[1]),
                quote=quote,
            ))
            symbol = c.symbol_name or "<无符号>"
            parts.append(
                f"- 相关片段（{c.hit.file_path}:{c.hit.line_range[0]}-{c.hit.line_range[1]}"
                f"，符号 {symbol}）"
            )
        content = f"根据检索到的 {len(citations)} 个相关片段，回答如下：\n" + "\n".join(parts)
        return AnswerResponse(
            refused=False,
            answer=CitedAnswer(content=content, citations=citations, confidence=confidence),
            config=self.config,
        )

    def verify_answers(self, queries: list[dict]) -> dict:
        """对一组查询跑管道，并核验每个可答答案的引用是否都能回到原文。

        返回 {"total", "answerable", "refused", "citations_total", "citations_ok", "bad": [...]}
        """
        summary = {"total": 0, "answerable": 0, "refused": 0,
                   "citations_total": 0, "citations_ok": 0, "bad": []}
        for q in queries:
            summary["total"] += 1
            response = self.answer(q["query"])
            if response.refused:
                summary["refused"] += 1
                continue
            summary["answerable"] += 1
            for citation in response.answer.citations:
                summary["citations_total"] += 1
                lines = self._files_by_path.get(citation.file_path, [])
                if verify_citation(citation, lines):
                    summary["citations_ok"] += 1
                else:
                    summary["bad"].append({
                        "query": q["query"],
                        "citation": f"{citation.file_path}:{citation.line_range[0]}-{citation.line_range[1]}",
                    })
        return summary
