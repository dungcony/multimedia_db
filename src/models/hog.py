import math
import numpy as np

from ..utils.l2nor import l2nor


class HOG:
    """
    Histogram of Oriented Gradients với 2 cải tiến chống nhiễu nền:

    1. Magnitude Threshold (mag_threshold_percentile):
       - Loại bỏ các pixel có gradient yếu (thuộc nền phẳng)
       - Chỉ giữ lại các cạnh mạnh (thường thuộc object)
       - Ví dụ percentile=30 → bỏ 30% gradient nhỏ nhất

    2. Center Crop (center_ratio):
       - Chỉ tính HOG trên vùng trung tâm
       - Giảm ảnh hưởng của background ở rìa ảnh
       - Dùng cùng center_ratio với Histogram để nhất quán
    """

    def __init__(self, img, bins, cell_size, block_size,
                 mag_threshold_percentile=30,
                 center_ratio=0.75):
        """
        Args:
            img                      : numpy array grayscale, shape (H, W), dtype uint8/float
            bins                     : số bin góc (thường = 9, tương ứng 0–180° mỗi bin 20°)
            cell_size                : kích thước ô pixel (e.g. 8)
            block_size               : số ô mỗi block (e.g. 2)
            mag_threshold_percentile : bỏ các gradient dưới percentile này (0 = giữ tất cả)
            center_ratio             : tỷ lệ vùng trung tâm (1.0 = toàn ảnh)
        """
        self.img                      = img
        self.bins                     = bins
        self.cell_size                = cell_size
        self.block_size               = block_size
        self.mag_threshold_percentile = mag_threshold_percentile
        self.center_ratio             = center_ratio

        self.vec      = None
        self.ang      = None
        self.mag      = None
        self.gx       = None
        self.gy       = None
        self.his_cell = None

        self.compute()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def compute(self):
        # Bước 0: crop trung tâm trước khi tính HOG
        work_img = self._crop_center(self.img)

        self._compute_gradients(work_img)
        self._compute_magnitude_angle()
        self._compute_cell_histogram()
        self._normalize_block_histogram()
        l2nor(self.vec)
        return self.vec

    # ------------------------------------------------------------------
    # Private — helpers
    # ------------------------------------------------------------------

    def _crop_center(self, img):
        """
        Cắt vùng trung tâm theo center_ratio.

        Ví dụ center_ratio=0.75, ảnh 224×224:
          mh = int(224 * 0.125) = 28
          → giữ rows [28 : 196], cols [28 : 196] (168×168)
        """
        if self.center_ratio >= 1.0:
            return img

        h, w = img.shape
        mh = int(h * (1.0 - self.center_ratio) / 2)
        mw = int(w * (1.0 - self.center_ratio) / 2)

        mh = min(mh, h // 4)
        mw = min(mw, w // 4)

        r0, r1 = mh, h - mh if mh > 0 else h
        c0, c1 = mw, w - mw if mw > 0 else w

        return img[r0:r1, c0:c1]

    # ------------------------------------------------------------------
    # Private — HOG core
    # ------------------------------------------------------------------

    def _compute_gradients(self, img):
        """
        Tính gradient Gx và Gy cho từng pixel bằng kernel [-1, 0, 1].

        Gx[h,w] = pad[h+1, w+2] - pad[h+1, w]   (gradient ngang)
        Gy[h,w] = pad[h,   w+1] - pad[h+2, w+1]  (gradient dọc)
        """
        he, wi = img.shape

        # Padding 1 pixel bốn phía (zero-padding)
        pad = np.zeros((he + 2, wi + 2), dtype=np.float64)
        pad[1:-1, 1:-1] = img

        self.gx = np.zeros((he, wi), dtype=np.float64)
        self.gy = np.zeros((he, wi), dtype=np.float64)

        for h in range(he):
            for w in range(wi):
                i = h + 1
                j = w + 1
                self.gx[h, w] = pad[i, j + 1] - pad[i, j - 1]
                self.gy[h, w] = pad[i - 1, j] - pad[i + 1, j]

    def _compute_magnitude_angle(self):
        """
        Tính magnitude và angle từ Gx, Gy.

        magnitude = sqrt(Gx² + Gy²)
        angle     = atan2(Gy, Gx) → [0, 180) (unsigned)
        """
        he, wi = self.gx.shape
        self.mag = np.zeros((he, wi), dtype=np.float64)
        self.ang = np.zeros((he, wi), dtype=np.float64)

        for h in range(he):
            for w in range(wi):
                self.mag[h, w] = math.sqrt(self.gx[h, w] ** 2 + self.gy[h, w] ** 2)

                deg = math.degrees(math.atan2(self.gy[h, w], self.gx[h, w]))
                if deg < 0:
                    deg += 180
                self.ang[h, w] = deg

    def _compute_cell_histogram(self):
        """
        Tính histogram gradient cho từng cell.

        Cải tiến — Magnitude Threshold:
          threshold = percentile(mag, mag_threshold_percentile)
          Pixel nào có mag < threshold → bỏ qua (không cộng vào histogram)

        Lý do: Nền phẳng (bầu trời, cát, đất) tạo gradient yếu nhưng nhiều.
        Loại bỏ chúng giúp histogram phản ánh đúng hơn hình dạng object.
        """
        he, wi = self.mag.shape
        n_cell_h = he // self.cell_size
        n_cell_w = wi // self.cell_size

        self.his_cell = np.zeros((n_cell_h, n_cell_w, self.bins), dtype=np.float64)

        # Tính ngưỡng magnitude một lần cho toàn ảnh
        if self.mag_threshold_percentile > 0:
            mag_threshold = np.percentile(self.mag, self.mag_threshold_percentile)
        else:
            mag_threshold = 0.0   # giữ tất cả (hành vi cũ)

        for ci in range(n_cell_h):
            for cj in range(n_cell_w):
                for i in range(self.cell_size):
                    for j in range(self.cell_size):
                        pi = ci * self.cell_size + i
                        pj = cj * self.cell_size + j

                        mag = self.mag[pi, pj]

                        # BỎ QUA pixel có gradient yếu (nhiễu nền)
                        if mag < mag_threshold:
                            continue

                        ang = self.ang[pi, pj]
                        bin_idx = min(int(ang / 20), self.bins - 1)
                        self.his_cell[ci, cj, bin_idx] += mag

    def _normalize_block_histogram(self):
        """
        Gộp các cell trong mỗi block → L2-normalize → nối thành vector cuối.

        Số block = (n_cell_h - block_size + 1) × (n_cell_w - block_size + 1)
        Mỗi block có block_size² × bins phần tử.
        """
        n_cell_h, n_cell_w, _ = self.his_cell.shape
        vec_block = []

        for ci in range(n_cell_h - self.block_size + 1):
            for cj in range(n_cell_w - self.block_size + 1):

                his_bloc = []
                for i in range(self.block_size):
                    for j in range(self.block_size):
                        cell = self.his_cell[ci + i, cj + j, :]
                        for val in cell:
                            his_bloc.append(val)

                his_bloc = self._l2_normalize(np.array(his_bloc))

                for val in his_bloc:
                    vec_block.append(val)

        self.vec = np.array(vec_block)

    def _l2_normalize(self, vector):
        """L2-normalize một vector, tránh chia-cho-0."""
        norm = math.sqrt(np.sum(vector ** 2))
        if norm > 1e-10:
            vector = vector / norm
        return vector