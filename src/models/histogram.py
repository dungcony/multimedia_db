import numpy as np

from ..utils.l2nor import l2nor


class Histogram:
    """
    HSV Color Histogram với 2 cải tiến chống nhiễu nền:

    1. Center Crop (center_ratio):
       - Chỉ lấy vùng trung tâm của ảnh để tính histogram
       - Object thường nằm giữa, nền thường ở rìa
       - Ví dụ center_ratio=0.7 → cắt 15% mỗi phía

    2. Spatial Grid Histogram (grid):
       - Chia ảnh (sau crop) thành grid G×G
       - Tính histogram riêng cho từng ô → nối lại
       - Giữ thông tin phân bố màu theo không gian
       - Phân biệt được "nền xám ở trên, vật thể nâu ở dưới"
         vs "nền xám ở dưới, vật thể nâu ở trên"

    Vector cuối: grid_h × grid_w × (bh × bs × bv) chiều
    Ví dụ grid=(3,3), bins=(8,4,4) → 9 × 128 = 1152 chiều
    """

    def __init__(self, img, bins, ranges,
                 center_ratio=0.75,
                 grid=(3, 3)):
        """
        Args:
            img          : numpy array HSV, shape (H, W, 3), dtype uint8/float
            bins         : tuple (bh, bs, bv) — số bin cho H, S, V
            ranges       : không dùng trực tiếp (giữ API cũ), scale cứng theo kênh
            center_ratio : tỷ lệ vùng trung tâm giữ lại (0 < ratio ≤ 1.0)
                           1.0 = toàn ảnh, 0.7 = giữ 70% giữa
            grid         : tuple (gh, gw) — chia ảnh thành gh×gw ô
        """
        self.img          = img
        self.bins         = bins
        self.ranges       = ranges
        self.center_ratio = center_ratio
        self.grid         = grid

        self.vec    = None
        self.vec_3D = None   # giữ để tương thích với code cũ (ô đầu tiên)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def compute(self):
        self._compute_histogram()
        return self.vec

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _crop_center(self, img):
        """
        Cắt vùng trung tâm theo center_ratio.
        Nếu ratio = 1.0 trả về ảnh gốc (không copy).
        """
        if self.center_ratio >= 1.0:
            return img

        h, w = img.shape[:2]
        mh = int(h * (1.0 - self.center_ratio) / 2)
        mw = int(w * (1.0 - self.center_ratio) / 2)

        # Đảm bảo không crop hết ảnh
        mh = min(mh, h // 4)
        mw = min(mw, w // 4)

        r0, r1 = mh, h - mh if mh > 0 else h
        c0, c1 = mw, w - mw if mw > 0 else w

        return img[r0:r1, c0:c1]

    def _histogram_patch(self, patch):
        """
        Tính histogram 3D cho một vùng ảnh HSV.

        Công thức bin:
          i = int(H / 180 * bh)   — H ∈ [0, 180)
          j = int(S / 256 * bs)   — S ∈ [0, 256)
          k = int(V / 256 * bv)   — V ∈ [0, 256)

        Returns:
            vec: shape (bh*bs*bv,), dtype float64, đã flatten (chưa l2nor)
            hist3d: shape (bh, bs, bv) — giữ để debug / vec_3D
        """
        bh, bs, bv = self.bins

        h_ch = patch[:, :, 0].astype(np.float64)
        s_ch = patch[:, :, 1].astype(np.float64)
        v_ch = patch[:, :, 2].astype(np.float64)

        hist3d = np.zeros((bh, bs, bv), dtype=np.float64)
        he, wi = patch.shape[:2]

        for r in range(he):
            for c in range(wi):
                i = min(int(h_ch[r, c] / 180.0 * bh), bh - 1)
                j = min(int(s_ch[r, c] / 256.0 * bs), bs - 1)
                k = min(int(v_ch[r, c] / 256.0 * bv), bv - 1)
                hist3d[i, j, k] += 1

        return hist3d.flatten(), hist3d

    def _compute_histogram(self):
        """
        Luồng chính:
          1. Center crop
          2. Chia grid gh × gw
          3. Tính histogram từng ô
          4. L2-normalize từng ô riêng → nối lại
          5. L2-normalize toàn bộ vector cuối
        """
        gh, gw = self.grid

        # Bước 1: crop trung tâm
        cropped = self._crop_center(self.img)
        h, w    = cropped.shape[:2]

        # Kích thước mỗi ô
        ch = h // gh
        cw = w // gw

        if ch == 0 or cw == 0:
            # Ảnh quá nhỏ → fallback toàn ảnh, không chia grid
            vec, self.vec_3D = self._histogram_patch(cropped)
            l2nor(vec)
            self.vec = vec
            return

        all_vecs = []

        for r in range(gh):
            for c in range(gw):
                r0, r1 = r * ch, (r + 1) * ch
                c0, c1 = c * cw, (c + 1) * cw
                patch = cropped[r0:r1, c0:c1]

                patch_vec, patch_3d = self._histogram_patch(patch)

                # Lưu ô đầu tiên vào vec_3D để tương thích API cũ
                if r == 0 and c == 0:
                    self.vec_3D = patch_3d

                # L2-normalize từng ô riêng trước khi nối
                # → các ô tối (ít pixel) không bị lấn át bởi ô sáng
                l2nor(patch_vec)
                all_vecs.append(patch_vec)

        # Nối tất cả ô
        self.vec = np.concatenate(all_vecs)

        # L2-normalize toàn bộ vector cuối
        l2nor(self.vec)