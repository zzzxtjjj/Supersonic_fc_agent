import math


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    计算两个向量的余弦相似度。
    """

    dot_product = 0.0
    norm_a_squared = 0.0
    norm_b_squared = 0.0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        norm_a_squared += a * a
        norm_b_squared += b * b

    norm_a = math.sqrt(norm_a_squared)
    norm_b = math.sqrt(norm_b_squared)

    if norm_a == 0 or norm_b == 0:
        raise ValueError("不能计算零向量的余弦相似度")

    cos_sim = dot_product / (norm_a * norm_b)

    return cos_sim

