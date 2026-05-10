import numpy as np

from ..utils.l2nor import l2nor


DEFAULT_LBP_BINS     = 256
DEFAULT_GLCM_LEVELS  = 8
DEFAULT_GLCM_DISTANCE = 1

# Offset 8 láng giềng theo thứ tự cố định (ngược chiều kim đồng hồ từ E)
#
#   p=3  p=2  p=1
#   p=4   c   p=0
#   p=5  p=6  p=7
#
OFFSET = [
    ( 0, +1),   # p=0  E
    (-1, +1),   # p=1  NE
    (-1,  0),   # p=2  N
    (-1, -1),   # p=3  NW
    ( 0, -1),   # p=4  W
    (+1, -1),   # p=5  SW
    (+1,  0),   # p=6  S
    (+1, +1),   # p=7  SE
]


class Texture:
    def __init__(
        self,
        img,
        lbp_bins=DEFAULT_LBP_BINS,
        glcm_levels=DEFAULT_GLCM_LEVELS,
        glcm_distance=DEFAULT_GLCM_DISTANCE,
    ):
        """
        Args:
            img          : numpy array, shape (H, W) hoặc (H, W, 3), dtype uint8
            lbp_bins     : số bin histogram LBP, mặc định 256
            glcm_levels  : số mức lượng tử hóa L cho GLCM, mặc định 8
            glcm_distance: khoảng cách pixel d cho GLCM (hướng ngang), mặc định 1
        """
        self.lbp_bins      = lbp_bins
        self.glcm_levels   = glcm_levels
        self.glcm_distance = glcm_distance

        # Bước 1: chuẩn hóa sang grayscale
        self.gray = self._to_grayscale(img)
        self.he, self.wi = self.gray.shape

        # Tính vector đặc trưng
        self.vec = self._compute()
        l2nor(self.vec)

    # ------------------------------------------------------------------
    # Bước 1 — Grayscale
    # ------------------------------------------------------------------

    def _to_grayscale(self, img):
        """
        Chuyển ảnh RGB sang grayscale.
        Nếu ảnh đã là grayscale (2D) thì giữ nguyên.

        Gray = 0.299R + 0.587G + 0.114B
        """
        if img.ndim == 2:
            return img.astype(np.float64)

        R = img[:, :, 0].astype(np.float64)
        G = img[:, :, 1].astype(np.float64)
        B = img[:, :, 2].astype(np.float64)

        gray = 0.299 * R + 0.587 * G + 0.114 * B  # shape (H, W), float64
        return gray

    # ------------------------------------------------------------------
    # Bước 2 — LBP
    # ------------------------------------------------------------------

    def _compute_lbp_histogram(self):
        """
        Tính histogram LBP từ self.gray.

        Quy trình:
          1. Pad ảnh thêm 1 pixel bốn phía (giá trị 0)
          2. Với mỗi pixel, so sánh 8 láng giềng với trung tâm → mã 8-bit
          3. Đếm histogram 256 bin rồi chuẩn hóa L2

        Returns:
            hist: shape (lbp_bins,), dtype float64, đã chuẩn hóa L2
        """
        # Ảnh quá nhỏ — không đủ láng giềng
        if self.he < 3 or self.wi < 3:
            return np.zeros(self.lbp_bins, dtype=np.float64)

        # --- Padding ---
        # Tạo ảnh lớn hơn 2 pixel mỗi chiều, vùng viền = 0.
        # Pixel gốc (h, w) → vị trí (h+1, w+1) trong pad.
        pad = np.zeros((self.he + 2, self.wi + 2), dtype=np.float64)
        pad[1:-1, 1:-1] = self.gray

        # --- Tính mã LBP từng pixel (vectorized theo 8 hướng) ---
        # center: giá trị pixel gốc, shape (H, W)
        center  = pad[1:-1, 1:-1]
        lbp_map = np.zeros((self.he, self.wi), dtype=np.uint8)

        for p, (dx, dy) in enumerate(OFFSET):
            # Cắt vùng láng giềng thứ p từ pad — không copy, O(1)
            row_start = 1 + dx
            row_end   = self.he + 1 + dx
            col_start = 1 + dy
            col_end   = self.wi + 1 + dy

            neighbor = pad[row_start:row_end, col_start:col_end]

            # Nếu láng giềng >= trung tâm → bật bit p
            # (neighbor >= center) : mảng bool shape (H, W)
            # .astype(uint8) * (1 << p) : 2^p tại các pixel thỏa mãn
            lbp_map += (neighbor >= center).astype(np.uint8) * (1 << p)

        # --- Histogram: đếm tần suất mỗi mã LBP (0–255) ---
        hist = np.zeros(self.lbp_bins, dtype=np.float64)
        for h in range(self.he):
            for w in range(self.wi):
                hist[lbp_map[h, w]] += 1

        # --- Chuẩn hóa L2 ---
        # h_hat = h / sqrt(sum(h^2))
        # Bất biến với kích thước ảnh (ảnh lớn → tổng đếm lớn hơn)
        norm = np.sqrt(np.sum(hist ** 2))
        if norm > 0:
            hist /= norm

        return hist

    # ------------------------------------------------------------------
    # Bước 3 — GLCM
    # ------------------------------------------------------------------

    def _compute_glcm_stats(self):
        """
        Tính 4 chỉ số thống kê GLCM từ self.gray.

        Quy trình:
          1. Lượng tử hóa grayscale xuống L mức
          2. Đếm cặp đồng xuất hiện theo hướng ngang, khoảng cách d
          3. Đối xứng hóa + chuẩn hóa thành xác suất P
          4. Tính Contrast, Energy, Homogeneity, Correlation từ P

        Returns:
            stats: shape (4,), dtype float64
                   [Contrast, Energy, Homogeneity, Correlation]
        """
        L = self.glcm_levels
        d = self.glcm_distance

        # --- Bước 3.1: Lượng tử hóa ---
        # q(x, y) = floor(gray[x, y] / (256 / L))
        # Phạm vi q: [0, L-1]
        q = np.floor(self.gray / (256.0 / L)).astype(np.int32)
        q = np.clip(q, 0, L - 1)   # đảm bảo không tràn index

        # --- Bước 3.2: Đếm cặp đồng xuất hiện ---
        # G[i, j] = số lần pixel mức i nằm cạnh pixel mức j (hướng ngang, cách d)
        G = np.zeros((L, L), dtype=np.float64)

        for x in range(self.he):
            for y in range(self.wi - d):
                i = q[x, y]
                j = q[x, y + d]
                G[i, j] += 1   # cặp gốc
                G[j, i] += 1   # đối xứng: cặp ngược chiều

        # --- Chuẩn hóa thành xác suất ---
        total = G.sum()
        if total == 0:
            return np.zeros(4, dtype=np.float64)
        P = G / total   # P[i, j] = xác suất cặp (i, j), shape (L, L)

        # --- Bước 3.3: Tính các chỉ số ---
        # Tạo lưới chỉ số r, c — dùng để tính vectorized
        r_idx = np.arange(L, dtype=np.float64)                      # [0, 1, ..., L-1]
        r_grid, c_grid = np.meshgrid(r_idx, r_idx, indexing='ij')   # shape (L, L)

        # Kỳ vọng
        # mu_r = sum_{r,c} r * P(r,c)
        mu_r = np.sum(r_grid * P)
        mu_c = np.sum(c_grid * P)

        # Độ lệch chuẩn
        # sigma_r = sqrt(sum_{r,c} (r - mu_r)^2 * P(r,c))
        sigma_r = np.sqrt(np.sum((r_grid - mu_r) ** 2 * P))
        sigma_c = np.sqrt(np.sum((c_grid - mu_c) ** 2 * P))

        # Contrast = sum_{r,c} (r - c)^2 * P(r,c)
        contrast = np.sum((r_grid - c_grid) ** 2 * P)

        # Energy = sum_{r,c} P(r,c)^2
        energy = np.sum(P ** 2)

        # Homogeneity = sum_{r,c} P(r,c) / (1 + |r - c|)
        homogeneity = np.sum(P / (1.0 + np.abs(r_grid - c_grid)))

        # Correlation = sum_{r,c} (r - mu_r)(c - mu_c) * P(r,c) / (sigma_r * sigma_c)
        # Edge case: ảnh đồng nhất hoàn toàn → sigma = 0 → gán correlation = 1
        if sigma_r < 1e-10 or sigma_c < 1e-10:
            correlation = 1.0
        else:
            correlation = np.sum((r_grid - mu_r) * (c_grid - mu_c) * P) / (sigma_r * sigma_c)

        return np.array([contrast, energy, homogeneity, correlation], dtype=np.float64)

    # ------------------------------------------------------------------
    # Bước 4 — Ghép vector
    # ------------------------------------------------------------------

    def _compute(self):
        """
        Ghép LBP histogram (256 chiều) và GLCM stats (4 chiều)
        thành vector đặc trưng 260 chiều.

        Returns:
            vec: shape (260,), dtype float64
        """
        lbp_hist  = self._compute_lbp_histogram()   # shape (256,)
        glcm_stats = self._compute_glcm_stats()      # shape (4,)

        # vec = [lbp_hist | glcm_stats]
        # Thứ tự: Contrast, Energy, Homogeneity, Correlation
        return np.concatenate([lbp_hist, glcm_stats])   # shape (260,)