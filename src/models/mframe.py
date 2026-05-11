import numpy as np
import cv2

from .rgb import RGB
from .histogram import Histogram
from .hog import HOG
from .texture import Texture


class MFrame:
    def __init__(self, frame, new_w, new_h, frame_idx=None, timestamp_sec=None):
        self.frame         = frame
        self.w             = new_w
        self.h             = new_h
        self.frame_idx     = frame_idx
        self.timestamp_sec = timestamp_sec

        self.hsv         = None
        self.gray        = None
        self.vec_his     = None
        self.vec_hog     = None
        self.vec_texture = None
        self.vec_cnn     = None
        self.vec         = None

        self._to_another_img()

    def _to_another_img(self):
        """Resize → HSV + grayscale."""
        resized   = cv2.resize(self.frame, (self.w, self.h))
        rgb       = RGB(resized)
        self.hsv  = rgb.to_hsv()
        self.gray = rgb.to_gray_scale()

    def compute_his(self, bins, ranges,
                    center_ratio=0.75,
                    grid=(3, 3)):
        hist         = Histogram(self.hsv, bins, ranges,
                                 center_ratio=center_ratio,
                                 grid=grid)
        self.vec_his = hist.compute()

    def compute_hog(self, bins, cell_size, block_size,
                    mag_threshold_percentile=30,
                    center_ratio=0.75):
        hog          = HOG(self.gray, bins, cell_size, block_size,
                          mag_threshold_percentile=mag_threshold_percentile,
                          center_ratio=center_ratio)
        self.vec_hog = hog.vec

    def compute_texture(self, lbp_bins, glcm_levels, glcm_distance,
                        edge_grid=(4, 4)):
        texture          = Texture(self.gray, lbp_bins, glcm_levels, glcm_distance,
                                   edge_grid=edge_grid)
        self.vec_texture = texture.vec

    def compute_vec(self, his_w=0.3, hog_w=1.0, text_w=0.7):
        self.vec = np.concatenate([
            self.vec_his     * his_w,
            self.vec_hog     * hog_w,
            self.vec_texture * text_w,
        ])

        # L2-normalize vector cuối để similarity không bị lệch bởi độ dài
        norm = np.linalg.norm(self.vec)
        if norm > 1e-10:
            self.vec /= norm
            
    def compute_to_cnn(self, cnn):
        """Trích vector CNN và set làm vector chính."""
        self.vec_cnn = cnn.extract(self.frame)
        self.vec = self.vec_cnn