
import math

def cosine_distance(vec_a, vec_b):
    """Tính cosine distance giữa 2 vector.

    cosine_distance = 1 - cosine_similarity
    Giá trị 0 → giống hoàn toàn, 1 → khác hoàn toàn.

    Args:
        vec_a: Vector numpy thứ nhất.
        vec_b: Vector numpy thứ hai.

    Returns:
        float: Cosine distance trong khoảng [0, 1].
    """
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for i in range(len(vec_a)):
        dot += vec_a[i] * vec_b[i]
        norm_a += vec_a[i] * vec_a[i]
        norm_b += vec_b[i] * vec_b[i]

    norm_a = math.sqrt(norm_a)
    norm_b = math.sqrt(norm_b)

    if norm_a == 0 or norm_b == 0:
        return 1.0

    similarity = dot / (norm_a * norm_b)
    # Clamp để tránh lỗi floating point
    similarity = max(-1.0, min(1.0, similarity))
    return 1.0 - similarity