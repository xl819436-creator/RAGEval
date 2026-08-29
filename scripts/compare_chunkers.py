"""对比两种分块器：块数、平均长度、符号完整率（Day 29 实验）。"""
import ast
from pathlib import Path

from rageval.chunkers import FixedChunker, PythonASTChunker, symbol_completeness

target = Path(__file__).resolve().parent.parent / "rageval" / "chunkers.py"
text = target.read_text(encoding="utf-8")

fixed = FixedChunker(chunk_size=200, overlap=20).chunk(text, str(target))
ast_chunks = PythonASTChunker(chunk_size=200, overlap=20).chunk(text, str(target))

tree = ast.parse(text)
symbols = [
    (n.lineno, n.end_lineno)
    for n in ast.walk(tree)
    if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
]

print(f"样本文件: {target}（{len(text)} 字符）")
print(f"符号总数: {len(symbols)}")
for name, chunks in [("FixedChunker", fixed), ("PythonASTChunker", ast_chunks)]:
    avg = sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0
    rate = symbol_completeness(chunks, symbols)
    print(f"{name}: 块数={len(chunks)}  平均长度={avg:.0f} 字符  符号完整率={rate:.0%}")