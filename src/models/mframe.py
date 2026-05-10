import numpy as np

from models.rgb import RGB

from .histogram import Histogram


class MFrame:
    def __init__(self,frame,new_w,new_h,frame_idx,timestamp_sec):
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
        # Chuyển đổi frame sang định dạng khác nếu cần (ví dụ: RGB → HSV)
        
        rgb = RGB(self.frame)
        rgb.resize(self.w,self.h)
        
        self.hsv = rgb.to_hsv()
        self.gray = rgb.to_gray()

    def compute_his(self,bins,ranges):
    
        hist = Histogram(self.hsv, bins, ranges)
        self.vec_his = hist.compute()
        
    def compute_hog(self,bins,cell_size,block_size):
        from .hog import HOG
        hog = HOG(self.gray,bins,cell_size,block_size)
        self.vec_hog = hog.compute()
        
    def compute_vec(self,his_w,hog_w):
        
        self.vec = np.concatenate((self.vec_his * his_w, self.vec_hog * hog_w))
    