"""
Histogram feature extraction utilities.
Cac ham pipeline: anh -> HSV -> histogram -> L2 normalize -> vector.
Dung chung cho ca notebook histo.ipynb va verify_histogram.py.
"""
import cv2
import numpy as np

# === Config mac dinh ===
TARGET_SIZE = (224, 224)
HIST_BINS = (16, 4, 4)  # H=16, S=4, V=4 => 256 chieu
HIST_RANGES = [0, 180, 0, 256, 0, 256]
TABLE_NAME = "histogram_features"


def preprocess_image(image_bgr: np.ndarray,
                     target_size: tuple = TARGET_SIZE) -> np.ndarray:
    """
    Resize anh ve target_size roi chuyen sang HSV.
    Input : BGR image (np.ndarray)
    Output: HSV image (np.ndarray)
    """
    resized = cv2.resize(image_bgr, target_size, interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)


def compute_hsv_histogram(image_hsv: np.ndarray,
                          bins: tuple = HIST_BINS,
                          ranges: list = None) -> np.ndarray:
    """
    Tinh histogram 3D tren HSV.
    Returns: vector 1D (flatten) co kich thuoc bins[0]*bins[1]*bins[2].
    """
    if ranges is None:
        ranges = HIST_RANGES
    hist = cv2.calcHist(
        images=[image_hsv],
        channels=[0, 1, 2],
        mask=None,
        histSize=list(bins),
        ranges=ranges,
    )
    return hist.flatten()


def normalize_l2(vector: np.ndarray) -> np.ndarray:
    """
    Chuan hoa L2: v_norm = v / ||v||_2
    Sau chuan hoa, ||v_norm||_2 = 1.
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def extract_histogram_vector(image_path: str,
                             target_size: tuple = TARGET_SIZE,
                             bins: tuple = HIST_BINS) -> np.ndarray:
    """
    Pipeline hoan chinh: doc anh -> resize -> HSV -> histogram -> L2 normalize.
    Returns: vector dac trung 1D da chuan hoa.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Cannot read: {image_path}")
    hsv = preprocess_image(img, target_size)
    hist = compute_hsv_histogram(hsv, bins)
    return normalize_l2(hist)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Cosine similarity giua 2 vector da L2-normalize (= dot product)."""
    return float(np.dot(v1, v2))


def search_similar(query_vec: np.ndarray,
                   db_rows: list,
                   top_k: int = 5) -> list:
    """Tim top_k vector tuong dong nhat trong db_rows."""
    results = []
    for row in db_rows:
        vec_db = np.array(row["feature_vector"], dtype=np.float64)
        sim = cosine_similarity(query_vec, vec_db)
        results.append({
            "video_id": row.get("video_id", "?"),
            "frame_path": row.get("frame_path", "?"),
            "similarity": sim,
        })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]
