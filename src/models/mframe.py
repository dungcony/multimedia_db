import numpy as np
import cv2

from .rgb import RGB
from .histogram import Histogram
from .hog import HOG
from .texture import Texture

class MFrame:
    def __init__(self, frame, new_w, new_h, frame_idx, timestamp_sec):
        self.frame = frame
        self.w = new_w
        self.h = new_h
        self.frame_idx = frame_idx
        self.timestamp_sec = timestamp_sec
        self.hsv = None
        self.gray = None
        self.vec_his = None
        self.vec_hog = None
        self.vec = None

        self._to_another_img()

    def _to_another_img(self):
        # Resize bang cv2 (nhanh), roi chuyen sang HSV va grayscale
        resized = cv2.resize(self.frame, (self.w, self.h))

        rgb = RGB(resized)
        self.hsv = rgb.to_hsv()
        self.gray = rgb.to_gray_scale()

    def compute_his(self, bins, ranges):
        hist = Histogram(self.hsv, bins, ranges)
        self.vec_his = hist.compute()

    def compute_hog(self, bins, cell_size, block_size):
        hog = HOG(self.gray, bins, cell_size, block_size)
        self.vec_hog = hog.vec
    
    def compute_texture(self, lbp_bins, glcm_levels, glcm_distance):
        texture = Texture(self.gray, lbp_bins, glcm_levels, glcm_distance)
        self.vec_texture = texture.vec

    def compute_vec(self, his_w, hog_w, text_w):
        self.vec = np.concatenate((self.vec_his * his_w, self.vec_hog * hog_w, self.vec_texture * text_w))