"""
histogram_custom.py — Tinh histogram HSV tu scratch (KHONG dung OpenCV).

Module nay cung cap day du pipeline:
    Anh -> Doc file -> Resize (bilinear) -> Chuyen HSV -> Histogram 3D -> L2 norm -> Vector

TAT CA thuat toan cot loi deu duoc viet thu cong:
    - Doc anh: dung Pillow (PIL) — chi de giai ma file JPEG/PNG, day la I/O
      thuan tuy, khong the tu viet bo giai ma JPEG from scratch.
    - Resize: Bilinear interpolation — viet thu cong.
    - BGR -> HSV: Viet thu cong theo cong thuc toan hoc.
    - Histogram 3D: Viet thu cong, dem tan suat pixel.
    - L2 normalize: Viet thu cong, khong dung np.linalg.norm.
    - Cosine similarity: Viet thu cong, khong dung np.dot.

KHONG import cv2 (OpenCV) o bat ky dau.
"""

import numpy as np
import math
from PIL import Image

# ============================================================
# 1. CAU HINH MAC DINH (giong histogram_utils.py)
# ============================================================
TARGET_SIZE = (224, 224)        # Kich thuoc anh sau resize (width, height)
HIST_BINS = (16, 4, 4)         # So bin cho H=16, S=4, V=4 => 256 chieu
HIST_RANGES = [0, 180, 0, 256, 0, 256]  # Pham vi gia tri moi kenh (theo chuan OpenCV HSV)
TABLE_NAME = "histogram_features"


# ============================================================
# 2. DOC ANH TU FILE (dung Pillow)
# ============================================================
def read_image(image_path: str) -> np.ndarray:
    """
    Doc anh tu file va tra ve mang numpy RGB, dtype uint8.

    Su dung Pillow (PIL) de giai ma file anh (JPEG, PNG, ...).
    Ly do: Giai ma JPEG can thuat toan DCT + Huffman rat phuc tap,
    khong hop ly de viet tu dau. Pillow chi lam nhiem vu I/O.

    Parameters
    ----------
    image_path : str
        Duong dan toi file anh.

    Returns
    -------
    np.ndarray
        Anh RGB, shape (H, W, 3), dtype uint8.
    """
    img = Image.open(str(image_path)).convert("RGB")
    return np.array(img, dtype=np.uint8)


# ============================================================
# 3. RESIZE ANH — BILINEAR INTERPOLATION (THU CONG)
# ============================================================
def resize_bilinear(image: np.ndarray, new_width: int, new_height: int) -> np.ndarray:
    """
    Resize anh bang Bilinear Interpolation — KHONG dung cv2.resize.

    === LY THUYET ===
    Khi resize anh, moi pixel (x', y') trong anh moi tuong ung voi
    mot vi tri (x, y) trong anh goc (co the la so thuc, khong phai
    nguyen). Ta can "noi suy" gia tri pixel tu 4 pixel lan can.

    Buoc 1: Tinh toa do tuong ung trong anh goc
        x = x' * (W_goc / W_moi)
        y = y' * (H_goc / H_moi)

    Buoc 2: Tim 4 pixel lan can
        (x0, y0) = (floor(x), floor(y))     — goc tren-trai
        (x1, y0)                              — goc tren-phai
        (x0, y1)                              — goc duoi-trai
        (x1, y1)                              — goc duoi-phai

    Buoc 3: Tinh trong so
        dx = x - x0  (khoang cach theo phuong ngang)
        dy = y - y0  (khoang cach theo phuong doc)

    Buoc 4: Noi suy
        pixel = (1-dx)*(1-dy)*P(x0,y0) + dx*(1-dy)*P(x1,y0)
              + (1-dx)*dy*P(x0,y1)     + dx*dy*P(x1,y1)

    Parameters
    ----------
    image : np.ndarray
        Anh goc, shape (H, W, 3), dtype uint8.
    new_width, new_height : int
        Kich thuoc moi.

    Returns
    -------
    np.ndarray
        Anh da resize, shape (new_height, new_width, 3), dtype uint8.
    """
    old_height, old_width = image.shape[0], image.shape[1]
    channels = image.shape[2] if image.ndim == 3 else 1

    # Chuyen sang float de tinh toan chinh xac
    img_float = image.astype(np.float64)

    # Tao mang ket qua
    resized = np.zeros((new_height, new_width, channels), dtype=np.float64)

    # Ty le scale giua anh goc va anh moi
    x_ratio = old_width / new_width
    y_ratio = old_height / new_height

    for row in range(new_height):
        for col in range(new_width):
            # Buoc 1: Toa do tuong ung trong anh goc
            # Dung (col + 0.5) * ratio - 0.5 de center-align
            x = (col + 0.5) * x_ratio - 0.5
            y = (row + 0.5) * y_ratio - 0.5

            # Buoc 2: 4 pixel lan can
            x0 = int(math.floor(x))
            y0 = int(math.floor(y))
            x1 = min(x0 + 1, old_width - 1)
            y1 = min(y0 + 1, old_height - 1)
            x0 = max(x0, 0)
            y0 = max(y0, 0)

            # Buoc 3: Trong so noi suy
            dx = x - math.floor(x)
            dy = y - math.floor(y)

            # Clamp dx, dy cho truong hop bien
            if x < 0:
                dx = 0.0
            if y < 0:
                dy = 0.0

            # Buoc 4: Noi suy song tuyen tinh (bilinear)
            # P = (1-dx)(1-dy)*P00 + dx*(1-dy)*P10 + (1-dx)*dy*P01 + dx*dy*P11
            w00 = (1.0 - dx) * (1.0 - dy)
            w10 = dx * (1.0 - dy)
            w01 = (1.0 - dx) * dy
            w11 = dx * dy

            resized[row, col] = (w00 * img_float[y0, x0]
                                 + w10 * img_float[y0, x1]
                                 + w01 * img_float[y1, x0]
                                 + w11 * img_float[y1, x1])

    return np.clip(resized, 0, 255).astype(np.uint8)


# ============================================================
# 4. CHUYEN DOI KHONG GIAN MAU RGB -> HSV (THU CONG)
# ============================================================
def rgb_to_hsv_manual(image_rgb: np.ndarray) -> np.ndarray:
    """
    Chuyen anh tu RGB sang HSV KHONG dung OpenCV.

    === LY THUYET ===
    Khong gian mau HSV gom 3 kenh:
      - H (Hue / Mau sac):     Goc tren vong tron mau (0-360 do).
                                Theo chuan OpenCV: H chia 2 => [0, 179].
      - S (Saturation / Bao hoa): Do dam cua mau, [0, 255].
      - V (Value / Gia tri):    Do sang, [0, 255].

    === TAI SAO DUNG HSV THAY VI RGB? ===
    - RGB tron lan thong tin mau sac va do sang. Cung mot mau do nhung
      sang/toi khac nhau se co gia tri RGB rat khac.
    - HSV tach biet: H la mau sac, S la do dam, V la do sang.
      => Histogram HSV ben vung hon voi thay doi anh sang.

    === CONG THUC ===
    Buoc 1: Chuan hoa RGB ve [0, 1]
        R' = R/255, G' = G/255, B' = B/255

    Buoc 2: Tim Cmax, Cmin, Delta
        Cmax = max(R', G', B')
        Cmin = min(R', G', B')
        Delta = Cmax - Cmin

    Buoc 3: Tinh H (Hue)
        Neu Delta == 0:   H = 0  (mau xam, khong co sac)
        Neu Cmax == R':   H = 60 * ((G' - B') / Delta  mod 6)
        Neu Cmax == G':   H = 60 * ((B' - R') / Delta + 2)    [KHAC voi BGR!]
        Neu Cmax == B':   H = 60 * ((R' - G') / Delta + 4)    [KHAC voi BGR!]

        Luu y: Voi anh RGB, thu tu kenh la R, G, B (khong phai B, G, R).
        H_opencv = H / 2  (de fit vao uint8: 0-179)

    Buoc 4: Tinh S (Saturation)
        Neu Cmax == 0: S = 0
        Nguoc lai:     S = (Delta / Cmax) * 255

    Buoc 5: Tinh V (Value)
        V = Cmax * 255

    Parameters
    ----------
    image_rgb : np.ndarray
        Anh RGB, shape (H, W, 3), dtype uint8.

    Returns
    -------
    np.ndarray
        Anh HSV, shape (H, W, 3), dtype uint8.
        Kenh H: [0, 179], S: [0, 255], V: [0, 255].
    """
    # --- Buoc 1: Chuan hoa ve float [0, 1] ---
    img = image_rgb.astype(np.float64) / 255.0

    r_ch = img[:, :, 0]
    g_ch = img[:, :, 1]
    b_ch = img[:, :, 2]

    # --- Buoc 2: Cmax, Cmin, Delta ---
    c_max = np.maximum(np.maximum(r_ch, g_ch), b_ch)
    c_min = np.minimum(np.minimum(r_ch, g_ch), b_ch)
    delta = c_max - c_min

    # --- Buoc 3: Tinh Hue ---
    h = np.zeros_like(delta)

    # Mask cho tung truong hop Cmax la kenh nao
    mask_delta = delta > 0  # Chi tinh khi co mau sac (khong phai xam)

    mask_r = (c_max == r_ch) & mask_delta
    mask_g = (c_max == g_ch) & mask_delta
    mask_b = (c_max == b_ch) & mask_delta

    # Cong thuc:
    h[mask_r] = 60.0 * (((g_ch[mask_r] - b_ch[mask_r]) / delta[mask_r]) % 6.0)
    h[mask_g] = 60.0 * (((b_ch[mask_g] - r_ch[mask_g]) / delta[mask_g]) + 2.0)
    h[mask_b] = 60.0 * (((r_ch[mask_b] - g_ch[mask_b]) / delta[mask_b]) + 4.0)

    # Dam bao H >= 0
    h[h < 0] += 360.0

    # OpenCV chia H cho 2 => [0, 179]
    h = h / 2.0

    # --- Buoc 4: Tinh Saturation ---
    s = np.zeros_like(delta)
    mask_nonzero = c_max > 0
    s[mask_nonzero] = (delta[mask_nonzero] / c_max[mask_nonzero]) * 255.0

    # --- Buoc 5: Tinh Value ---
    v = c_max * 255.0

    # --- Ghep va chuyen uint8 ---
    hsv = np.stack([h, s, v], axis=-1)
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)

    return hsv


# ============================================================
# 5. TIEN XU LY ANH: Resize + Chuyen HSV
# ============================================================
def preprocess_image(image_rgb: np.ndarray,
                     target_size: tuple = TARGET_SIZE) -> np.ndarray:
    """
    Resize anh ve target_size roi chuyen sang HSV (tat ca thu cong).

    Parameters
    ----------
    image_rgb : np.ndarray
        Anh RGB goc, dtype uint8.
    target_size : tuple
        (width, height) mong muon.

    Returns
    -------
    np.ndarray
        Anh HSV da resize, dtype uint8.
    """
    w, h = target_size
    resized = resize_bilinear(image_rgb, w, h)
    return rgb_to_hsv_manual(resized)


# ============================================================
# 6. TINH HISTOGRAM 3D THU CONG
# ============================================================
def compute_hsv_histogram(image_hsv: np.ndarray,
                          bins: tuple = HIST_BINS,
                          ranges: list = None) -> np.ndarray:
    """
    Tinh histogram 3D tren anh HSV — KHONG dung cv2.calcHist.

    === HISTOGRAM LA GI? ===
    Histogram la bang dem tan suat: voi moi pixel, xac dinh no thuoc
    "ngan" (bin) nao dua tren gia tri kenh mau, roi tang bo dem cua
    ngan do len 1.

    === HISTOGRAM 3D ===
    Voi 3 kenh (H, S, V) va so bin (bH, bS, bV), ta co mot mang 3 chieu:
        hist[i][j][k] = so pixel co:
            - H thuoc bin thu i  (trong bH bin)
            - S thuoc bin thu j  (trong bS bin)
            - V thuoc bin thu k  (trong bV bin)

    === CACH TINH BIN INDEX ===
    Cho kenh co pham vi [lo, hi) va n bins:
        bin_width = (hi - lo) / n
        index = floor((value - lo) / bin_width)
        index = clamp(index, 0, n-1)

    Vi du: H co range [0, 180), 16 bins:
        bin_width = 180/16 = 11.25
        Pixel H=50 => bin = floor(50/11.25) = floor(4.44) = 4

    === TAI SAO HISTOGRAM 3D THAY VI 3 HISTOGRAM 1D? ===
    Histogram 3D giu duoc TUONG QUAN giua cac kenh. Vi du: pixel
    "do + sang" va "do + toi" se o cac bin khac nhau trong hist 3D,
    nhung bi gop chung neu chi dung hist 1D cho kenh H.

    === FLATTEN ===
    Sau khi tinh, flatten mang 3D thanh vector 1D de su dung lam
    dac trung (feature vector) cho viec so sanh va tim kiem.

    Parameters
    ----------
    image_hsv : np.ndarray
        Anh HSV, shape (H, W, 3), dtype uint8.
    bins : tuple
        (bins_H, bins_S, bins_V).
    ranges : list
        [H_min, H_max, S_min, S_max, V_min, V_max].

    Returns
    -------
    np.ndarray
        Vector 1D (flatten), shape (bins_H * bins_S * bins_V,).
    """
    if ranges is None:
        ranges = HIST_RANGES

    bins_h, bins_s, bins_v = bins
    h_min, h_max = ranges[0], ranges[1]
    s_min, s_max = ranges[2], ranges[3]
    v_min, v_max = ranges[4], ranges[5]

    # --- Tinh bin_width ---
    h_width = (h_max - h_min) / bins_h
    s_width = (s_max - s_min) / bins_s
    v_width = (v_max - v_min) / bins_v

    # --- Tach 3 kenh ---
    h_ch = image_hsv[:, :, 0].astype(np.float64)
    s_ch = image_hsv[:, :, 1].astype(np.float64)
    v_ch = image_hsv[:, :, 2].astype(np.float64)

    # --- Tinh chi so bin cho tung pixel ---
    # Dung phep tinh vectorized (nhanh hon vong lap Python nhieu lan)
    h_idx = np.clip(((h_ch - h_min) / h_width).astype(np.int32), 0, bins_h - 1)
    s_idx = np.clip(((s_ch - s_min) / s_width).astype(np.int32), 0, bins_s - 1)
    v_idx = np.clip(((v_ch - v_min) / v_width).astype(np.int32), 0, bins_v - 1)

    # --- Khoi tao histogram 3D ---
    hist = np.zeros((bins_h, bins_s, bins_v), dtype=np.float64)

    # --- Dem tan suat ---
    # np.add.at: cong 1 vao hist tai vi tri (h_idx, s_idx, v_idx)
    # cho moi pixel. Khac fancy indexing (hist[h,s,v] += 1) vi
    # add.at xu ly dung khi nhieu pixel trung index.
    h_flat = h_idx.ravel()
    s_flat = s_idx.ravel()
    v_flat = v_idx.ravel()
    np.add.at(hist, (h_flat, s_flat, v_flat), 1)

    return hist.flatten()


# ============================================================
# 7. CHUAN HOA L2 THU CONG
# ============================================================
def normalize_l2(vector: np.ndarray) -> np.ndarray:
    """
    Chuan hoa L2 — KHONG dung np.linalg.norm.

    === CONG THUC ===
    ||v||_2 = sqrt(v1^2 + v2^2 + ... + vn^2)
    v_norm = v / ||v||_2

    === TAI SAO CAN CHUAN HOA? ===
    - Loai bo anh huong cua tong so pixel (anh to/nho khac nhau).
    - Sau chuan hoa: ||v|| = 1 (vector don vi).
    - Cosine similarity = dot product (nhanh hon).
    """
    sum_sq = 0.0
    for val in vector:
        sum_sq += val * val
    norm = math.sqrt(sum_sq)

    if norm == 0:
        return vector
    return vector / norm


# ============================================================
# 8. PIPELINE HOAN CHINH
# ============================================================
def extract_histogram_vector(image_path: str,
                             target_size: tuple = TARGET_SIZE,
                             bins: tuple = HIST_BINS) -> np.ndarray:
    """
    Pipeline: doc anh -> resize -> HSV -> histogram 3D -> L2 normalize.

    === QUY TRINH ===
    1. Doc anh (Pillow) — giai ma file JPEG/PNG thanh mang pixel RGB
    2. Resize (bilinear interpolation thu cong) — dong nhat kich thuoc
    3. Chuyen RGB -> HSV (thu cong) — tach biet mau sac / do sang
    4. Tinh histogram 3D (thu cong) — dem phan bo mau
    5. Chuan hoa L2 (thu cong) — dong nhat do lon vector

    Returns
    -------
    np.ndarray
        Vector dac trung 1D da chuan hoa, shape (256,) voi config mac dinh.
    """
    # 1. Doc anh
    img_rgb = read_image(image_path)

    # 2 + 3. Resize va chuyen HSV
    hsv = preprocess_image(img_rgb, target_size)

    # 4. Histogram 3D
    hist = compute_hsv_histogram(hsv, bins)

    # 5. Chuan hoa L2
    return normalize_l2(hist)


# ============================================================
# 9. COSINE SIMILARITY (THU CONG)
# ============================================================
def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Cosine similarity — KHONG dung np.dot.

    === CONG THUC ===
    cos(v1, v2) = (v1 . v2) / (||v1|| * ||v2||)

    Neu da L2-normalize: cos = v1 . v2 (dot product)

    === Y NGHIA ===
    - 1:  giong hoan toan
    - 0:  khong lien quan
    - -1: doi lap
    """
    dot = 0.0
    norm1_sq = 0.0
    norm2_sq = 0.0

    for i in range(len(v1)):
        dot += v1[i] * v2[i]
        norm1_sq += v1[i] * v1[i]
        norm2_sq += v2[i] * v2[i]

    norm1 = math.sqrt(norm1_sq)
    norm2 = math.sqrt(norm2_sq)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


# ============================================================
# 10. TIM KIEM ANH TUONG TU
# ============================================================
def search_similar(query_vec: np.ndarray,
                   db_rows: list,
                   top_k: int = 5) -> list:
    """
    Tim top_k anh tuong dong nhat (brute-force).

    === THUAT TOAN ===
    Duyet tat ca dong trong DB, tinh cosine similarity voi query,
    sap xep giam dan, lay top_k. Do phuc tap: O(n).
    """
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


# ============================================================
# 11. MAIN — CHAY THU
# ============================================================
if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[3]
    keyframe_dir = project_root / "public" / "keyframes"

    sample = None
    for f in keyframe_dir.rglob("*.jpg"):
        sample = str(f)
        break

    if sample is None:
        print("[ERROR] Khong tim thay anh trong", keyframe_dir)
    else:
        print(f"Anh mau: {sample}")
        print()

        # Test pipeline
        vec = extract_histogram_vector(sample)
        norm_val = math.sqrt(sum(v * v for v in vec))
        print(f"Vector shape : {vec.shape}")
        print(f"Vector L2 norm: {norm_val:.6f}  (phai = 1.0)")
        print(f"Vector min   : {vec.min():.6f}")
        print(f"Vector max   : {vec.max():.6f}")
        print(f"Sum histogram: {compute_hsv_histogram(preprocess_image(read_image(sample))).sum():.0f}")
        print(f"  (phai = {TARGET_SIZE[0]} x {TARGET_SIZE[1]} = {TARGET_SIZE[0]*TARGET_SIZE[1]})")
