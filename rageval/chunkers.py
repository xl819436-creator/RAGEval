"""Day 29：两种分块器——FixedChunker 与 PythonASTChunker。"""

import ast
from dataclasses import dataclass


@dataclass
class Chunk:
    """一个分块结果：文本 + 可追溯到原文件的路径和行号。"""

    path: str  # 原文件路径
    start_line: int  # 起始行号（1 起）
    end_line: int  # 结束行号（含）
    content: str  # 块内容
    symbol_name: str | None = None  # 符号名（AST 分块才有）
    chunk_type: str = "fixed"  # fixed / ast
    fallback_reason: str | None = None  # 降级原因（AST 失败时记录）


class FixedChunker:
    """固定长度分块：按字符数切，块间可重叠 overlap 个字符。"""

    def __init__(self, chunk_size: int = 200, overlap: int = 20):
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须 > 0")
        if not (0 <= overlap < chunk_size):
            raise ValueError("overlap 必须在 [0, chunk_size) 之间")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, path: str) -> list[Chunk]:
        chunks = []
        start = 0
        n = len(text)
        step = self.chunk_size - self.overlap  # 每次前进的步长
        while start < n:
            end = min(start + self.chunk_size, n)
            chunks.append(
                Chunk(
                    path=path,
                    start_line=text.count("\n", 0, start) + 1,
                    end_line=text.count("\n", 0, end) + 1,
                    content=text[start:end],
                    chunk_type="fixed",
                )
            )
            if end >= n:
                break
            start += step
        return chunks


class PythonASTChunker:
    """AST 分块：按 Python 语法结构（类/函数/异步函数）切块。"""

    def __init__(self, chunk_size: int = 200, overlap: int = 20):
        self._fallback = FixedChunker(chunk_size, overlap)

    def chunk(self, text: str, path: str) -> list[Chunk]:
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            # 降级：语法错误文件用固定分块，绝不崩溃
            fallback = self._fallback.chunk(text, path)
            for c in fallback:
                c.fallback_reason = f"syntax error at line {exc.lineno}: {exc.msg}"
            return fallback

        chunks = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                content = ast.get_source_segment(text, node) or ""
                chunks.append(
                    Chunk(
                        path=path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        content=content,
                        symbol_name=node.name,
                        chunk_type="ast",
                    )
                )
        if not chunks:
            # 没有类/函数（只有 import、注释、表达式）→ 退化为固定分块
            fallback = self._fallback.chunk(text, path)
            for c in fallback:
                c.fallback_reason = "no class/function symbols found"
            return fallback
        return chunks


def symbol_completeness(chunks: list[Chunk], symbols: list[tuple[int, int]]) -> float:
    """符号完整率：完整落进某个块的符号占比（实战 1 的量化指标）。"""
    if not symbols:
        return 1.0
    complete = 0
    for s_start, s_end in symbols:
        if any(c.start_line <= s_start and c.end_line >= s_end for c in chunks):
            complete += 1
    return complete / len(symbols)