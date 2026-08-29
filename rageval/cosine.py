"""Day 28：余弦相似度（手工向量演示）。为什么叫余弦：两个向量的夹角越小越像，cos(0°)=1 最像。"""

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """两个向量夹角的余弦值：1=完全相同，0=垂直无关，-1=完全相反。"""
    dot = sum(x * y for x, y in zip(a, b))       # 点积：对应位置相乘再求和
    norm_a = math.sqrt(sum(x * x for x in a))    # a 的模长
    norm_b = math.sqrt(sum(y * y for y in b))    # b 的模长
    if norm_a == 0 or norm_b == 0:
        return 0.0  # 向量全 0 无法算角度，返回 0
    return dot / (norm_a * norm_b)               # 余弦公式


if __name__ == "__main__":
    a = [1, 0, 0]   # 三维空间里的"向东"
    b = [1, 0, 0]   # 也是向东
    c = [0, 1, 0]   # 向北
    print("a·a =", cosine_similarity(a, b))  # 预期 1.0（完全一样）
    print("a·c =", cosine_similarity(a, c))  # 预期 0.0（垂直，无关）