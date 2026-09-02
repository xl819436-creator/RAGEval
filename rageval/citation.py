"""Day 32：引用（Citation）数据模型与核验。

为什么要有 Citation：答案里的每一句都要能"回到原文"——
file_path + line_range 指出在哪，symbol_name 指出是什么，quote 是原文摘录，
verify_citation 检查摘录确实在该文件对应行，防止引用指向无关行。
"""

from dataclasses import dataclass


@dataclass
class Citation:
    """一条可追溯引用：指向语料里的一个具体位置。"""

    file_path: str
    symbol_name: str | None
    line_range: tuple[int, int]
    quote: str  # 原文摘录（用于核验）


def verify_citation(citation: Citation, file_lines: list[str]) -> bool:
    """核验引用：quote 是否确实出现在 file_lines 的 line_range 内。

    为什么按行范围核验：要求引用能回到原文，防止模型/管道编造出处。
    """
    start, end = citation.line_range
    if start < 1 or end > len(file_lines) or start > end:
        return False
    region = "\n".join(file_lines[start - 1:end])
    return citation.quote.strip() in region
