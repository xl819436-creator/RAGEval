"""Day 29 分块器测试。"""
from rageval.chunkers import FixedChunker, PythonASTChunker, symbol_completeness

SAMPLE = '''"""模块 docstring"""
import os


class Greeter:
    """打招呼类"""

    def hello(self):
        return "hi"


async def fetch():
    return 1
'''


def test_fixed_chunker_counts():
    text = "a" * 500
    chunks = FixedChunker(chunk_size=200, overlap=0).chunk(text, "x.py")
    assert len(chunks) == 3  # 500 / 200 = 2.5 -> 3 块


def test_fixed_chunker_overlap():
    text = "a" * 300
    chunks = FixedChunker(chunk_size=200, overlap=50).chunk(text, "x.py")
    assert len(chunks) == 2  # 步长 150 -> 起点 0, 150
    assert chunks[0].end_line >= chunks[1].start_line


def test_ast_chunker_finds_symbols():
    chunks = PythonASTChunker().chunk(SAMPLE, "sample.py")
    names = [c.symbol_name for c in chunks]
    assert "Greeter" in names
    assert "hello" in names
    assert "fetch" in names
    assert all(c.chunk_type == "ast" for c in chunks)


def test_ast_chunker_keeps_function_whole():
    # 实战 1：函数不能从中间切断
    chunks = PythonASTChunker().chunk(SAMPLE, "sample.py")
    fetch = [c for c in chunks if c.symbol_name == "fetch"][0]
    assert "return 1" in fetch.content  # 函数体完整


def test_ast_chunker_line_numbers():
    # 实战 3：行号能回到原文件
    chunks = PythonASTChunker().chunk(SAMPLE, "sample.py")
    hello = [c for c in chunks if c.symbol_name == "hello"][0]
    assert hello.start_line == 8
    assert hello.end_line == 9


def test_fallback_on_syntax_error():
    # 实战 2：语法错误文件自动降级
    text = "def broken(:\n    pass"
    chunks = PythonASTChunker().chunk(text, "bad.py")
    assert len(chunks) >= 1
    assert all(c.fallback_reason is not None for c in chunks)
    assert "syntax error" in chunks[0].fallback_reason


def test_empty_file():
    chunks = PythonASTChunker().chunk("", "empty.py")
    assert chunks == []  # 空文件 -> 空块列表


def test_comment_only_file():
    text = "# 只有注释\n# 没有代码\n"
    chunks = PythonASTChunker().chunk(text, "comment.py")
    assert len(chunks) >= 1
    assert all(c.fallback_reason is not None for c in chunks)


def test_symbol_completeness():
    # 对比两种 chunker 的符号完整率
    import ast as ast_mod

    tree = ast_mod.parse(SAMPLE)
    symbols = [
        (n.lineno, n.end_lineno)
        for n in ast_mod.walk(tree)
        if isinstance(n, (ast_mod.ClassDef, ast_mod.FunctionDef, ast_mod.AsyncFunctionDef))
    ]
    fixed = FixedChunker(chunk_size=30, overlap=0).chunk(SAMPLE, "sample.py")
    ast_chunks = PythonASTChunker().chunk(SAMPLE, "sample.py")
    assert symbol_completeness(ast_chunks, symbols) == 1.0   # AST 100% 完整
    assert symbol_completeness(fixed, symbols) < 1.0         # 固定分块被切断