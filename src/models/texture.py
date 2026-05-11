import numpy as np

from ..utils.l2nor import l2nor


DEFAULT_LBP_BINS      = 256
DEFAULT_GLCM_LEVELS   = 8
DEFAULT_GLCM_DISTANCE = 1
DEFAULT_EDGE_GRID     = (4, 4)   # grid tính mật độ cạnh

# Offset 8 láng giềng (ngược chiều kim đồng hồ từ E)
#
#   p=3  p=2  p=1
#   p=4   c   p=0
#   p=5  p=6  p=7
#
OFFSET = [
    ( 0, +1),  # p=0  E
    (-1, +1),  # p=1  NE
    (-1,  0),  # p=2  N
    (-1, -1),  # p=3  NW
    ( 0, -1),  # p=4  W
    (+1, -1),  # p=5  SW
    (+1,  0),  # p=6  S
    (+1, +1),  # p=7  SE
]


class Texture:

    def __init__(
        self,
        img,
        lbp_bins=DEFAULT_LBP_BINS,
        glcm_levels=DEFAULT_GLCM_LEVELS,
        glcm_distance=DEFAULT_GLCM_DISTANCE,
        edge_grid=DEFAULT_EDGE_GRID,
    ):
        self.lbp_bins      = lbp_bins
        self.glcm_levels   = glcm_levels
        self.glcm_distance = glcm_distance
        self.edge_grid     = edge_grid

        # Bước 1: chuẩn hóa sang grayscale
        self.gray      = self._to_grayscale(img)
        self.he, self.wi = self.gray.shape

        # Tính vector đặc trưng
        self.vec = self._compute()
        l2nor(self.vec)
        
    def _compute_lbp_histogram(self):
        if self.he < 3 or self.wi < 3:
            return np.zeros(self.lbp_bins, dtype=np.float64)

        pad = np.zeros((self.he + 2, self.wi + 2), dtype=np.float64)
        pad[1:-1, 1:-1] = self.gray

        center  = pad[1:-1, 1:-1]
        lbp_map = np.zeros((self.he, self.wi), dtype=np.uint8)

        for p, (dx, dy) in enumerate(OFFSET):
            row_start = 1 + dx
            row_end   = self.he + 1 + dx
            col_start = 1 + dy
            col_end   = self.wi + 1 + dy

            neighbor = pad[row_start:row_end, col_start:col_end]
            lbp_map += (neighbor >= center).astype(np.uint8) * (1 << p)

        hist = np.zeros(self.lbp_bins, dtype=np.float64)
        for h in range(self.he):
            for w in range(self.wi):
                hist[lbp_map[h, w]] += 1

        norm = np.sqrt(np.sum(hist ** 2))
        if norm > 0:
            hist /= norm

        return hist

    def _compute_glcm_stats(self):
        L = self.glcm_levels
        d = self.glcm_distance

        q = np.floor(self.gray / (256.0 / L)).astype(np.int32)
        q = np.clip(q, 0, L - 1)

        G = np.zeros((L, L), dtype=np.float64)

        for x in range(self.he):
            for y in range(self.wi - d):
                i = q[x, y]
                j = q[x, y + d]
                G[i, j] += 1
                G[j, i] += 1

        total = G.sum()
        if total == 0:
            return np.zeros(4, dtype=np.float64)
        P = G / total

        r_idx = np.arange(L, dtype=np.float64)
        r_grid, c_grid = np.meshgrid(r_idx, r_idx, indexing='ij')

        mu_r    = np.sum(r_grid * P)
        mu_c    = np.sum(c_grid * P)
        sigma_r = np.sqrt(np.sum((r_grid - mu_r) ** 2 * P))
        sigma_c = np.sqrt(np.sum((c_grid - mu_c) ** 2 * P))

        contrast    = np.sum((r_grid - c_grid) ** 2 * P)
        energy      = np.sum(P ** 2)
        homogeneity = np.sum(P / (1.0 + np.abs(r_grid - c_grid)))

        if sigma_r < 1e-10 or sigma_c < 1e-10:
            correlation = 1.0
        else:
            correlation = np.sum(
                (r_grid - mu_r) * (c_grid - mu_c) * P
            ) / (sigma_r * sigma_c)

        return np.array([contrast, energy, homogeneity, correlation], dtype=np.float64)


    def _compute_edge_density(self):
        gh, gw = self.edge_grid
        he, wi = self.he, self.wi

        # --- Tính gradient magnitude ---
        pad = np.zeros((he + 2, wi + 2), dtype=np.float64)
        pad[1:-1, 1:-1] = self.gray

        # Vectorized — nhanh hơn vòng lặp pixel
        gx = pad[1:-1, 2:] - pad[1:-1, :-2]      # shape (H, W)
        gy = pad[:-2, 1:-1] - pad[2:, 1:-1]       # shape (H, W)
        mag = np.sqrt(gx ** 2 + gy ** 2)           # shape (H, W)

        # --- Tính mật độ trung bình từng vùng ---
        ch = he // gh
        cw = wi // gw

        if ch == 0 or cw == 0:
            # Ảnh quá nhỏ
            return np.zeros(gh * gw, dtype=np.float64)

        density = np.zeros(gh * gw, dtype=np.float64)

        for r in range(gh):
            for c in range(gw):
                r0, r1 = r * ch, (r + 1) * ch
                c0, c1 = c * cw, (c + 1) * cw
                patch_mag = mag[r0:r1, c0:c1]
                density[r * gw + c] = patch_mag.mean()

        # --- L2-normalize ---
        norm = np.sqrt(np.sum(density ** 2))
        if norm > 1e-10:
            density /= norm

        return density

    def _compute_gabor_features(self):
        from scipy.ndimage import convolve
        
        frequencies = [0.1, 0.25, 0.4]   # tần số không gian (thấp→cao)
        thetas      = [0, 45, 90, 135]   # hướng (độ)
        ksize       = 15                  # kích thước kernel
        sigma       = 3.0
        
        features = []
        half = ksize // 2
        
        for freq in frequencies:
            for theta_deg in thetas:
                theta = np.radians(theta_deg)
                
                # Xây dựng kernel Gabor
                kernel = np.zeros((ksize, ksize), dtype=np.float64)
                for u in range(ksize):
                    for v in range(ksize):
                        x = u - half
                        y = v - half
                        x_rot = x * np.cos(theta) + y * np.sin(theta)
                        y_rot = -x * np.sin(theta) + y * np.cos(theta)
                        gauss = np.exp(-(x_rot**2 + y_rot**2) / (2 * sigma**2))
                        kernel[u, v] = gauss * np.cos(2 * np.pi * freq * x_rot)
                
                # Convolution với ảnh
                response = convolve(self.gray, kernel)
                
                features.append(response.mean())
                features.append(response.std())
        
        vec = np.array(features, dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec /= norm
        return vec  # shape: (2 * 3 * 4,) = 24 chiều
    
    def _compute_hu_moments(self):
        # Tính gradient magnitude
        pad = np.zeros((self.he + 2, self.wi + 2), dtype=np.float64)
        pad[1:-1, 1:-1] = self.gray
        gx  = pad[1:-1, 2:] - pad[1:-1, :-2]
        gy  = pad[:-2, 1:-1] - pad[2:, 1:-1]
        mag = np.sqrt(gx**2 + gy**2)
        
        # Binary map: giữ 40% edge mạnh nhất
        threshold = np.percentile(mag, 60)
        binary    = (mag >= threshold).astype(np.float64)
        
        # Raw moments
        h_idx = np.arange(self.he, dtype=np.float64)
        w_idx = np.arange(self.wi, dtype=np.float64)
        W, H  = np.meshgrid(w_idx, h_idx)  # W[r,c]=c, H[r,c]=r
        
        m00 = binary.sum()
        if m00 < 1e-10:
            return np.zeros(7, dtype=np.float64)
        
        m10 = (H * binary).sum()
        m01 = (W * binary).sum()
        m20 = (H**2 * binary).sum()
        m02 = (W**2 * binary).sum()
        m11 = (H * W * binary).sum()
        m30 = (H**3 * binary).sum()
        m03 = (W**3 * binary).sum()
        m21 = (H**2 * W * binary).sum()
        m12 = (H * W**2 * binary).sum()
        
        # Centroid
        cx = m10 / m00
        cy = m01 / m00
        
        # Central moments
        mu20 = m20 / m00 - cx**2
        mu02 = m02 / m00 - cy**2
        mu11 = m11 / m00 - cx * cy
        mu30 = (m30 - 3*m10*m20/m00 + 2*(m10**2)*m10/m00**2) / m00
        mu03 = (m03 - 3*m01*m02/m00 + 2*(m01**2)*m01/m00**2) / m00
        mu21 = (m21 - 2*cx*m11 - cy*m20 + 2*cx**2*m01) / m00
        mu12 = (m12 - 2*cy*m11 - cx*m02 + 2*cy**2*m10) / m00
        
        # 7 Hu Invariants
        hu = np.zeros(7, dtype=np.float64)
        hu[0] = mu20 + mu02
        hu[1] = (mu20 - mu02)**2 + 4*mu11**2
        hu[2] = (mu30 - 3*mu12)**2 + (3*mu21 - mu03)**2
        hu[3] = (mu30 + mu12)**2 + (mu21 + mu03)**2
        hu[4] = (mu30 - 3*mu12)*(mu30 + mu12)*((mu30+mu12)**2 - 3*(mu21+mu03)**2) + \
                (3*mu21 - mu03)*(mu21+mu03)*(3*(mu30+mu12)**2 - (mu21+mu03)**2)
        hu[5] = (mu20-mu02)*((mu30+mu12)**2-(mu21+mu03)**2) + 4*mu11*(mu30+mu12)*(mu21+mu03)
        hu[6] = (3*mu21-mu03)*(mu30+mu12)*((mu30+mu12)**2-3*(mu21+mu03)**2) - \
                (mu30-3*mu12)*(mu21+mu03)*(3*(mu30+mu12)**2-(mu21+mu03)**2)
        
        # Log transform (Hu moments có range rất lớn)
        hu_log = np.sign(hu) * np.log1p(np.abs(hu))
        
        norm = np.linalg.norm(hu_log)
        if norm > 1e-10:
            hu_log /= norm
        return hu_log   # shape (7,)
    
    def _compute(self):
        lbp_hist     = self._compute_lbp_histogram()   # 256
        glcm_stats   = self._compute_glcm_stats()      # 4
        edge_density = self._compute_edge_density()    # 16
        gabor_feat   = self._compute_gabor_features()  # 24
        hu_moments   = self._compute_hu_moments()      # 7

        return np.concatenate([
            lbp_hist,      # texture vi mô
            glcm_stats,    # texture thống kê
            edge_density,  # phân bố cạnh theo vùng
            gabor_feat,    # tần số + hướng theo vùng  ← mới
            hu_moments,    # hình dạng tổng thể        ← mới
        ])
        # Tổng: 256 + 4 + 16 + 24 + 7 = 307 chiều