import numpy as np
import math


class Histogram:
    def __init__(self,img,bins,ranges):
        self.vec = None
        self.vec_3D = None
        self.ranges = ranges
        self.bins = bins
        self.img = img

    def compute(self):
        
        self._compute_histogram()
        self._normalize_vec_1D()
        
        return self.vec

    def _compute_histogram(self):
        bh,bs,bv = self.bins
        h_ch = self.img[:,:,0].astype(np.float64)
        s_ch = self.img[:,:,1].astype(np.float64)
        v_ch = self.img[:,:,2].astype(np.float64)

        # tạo mảng 3 chiều có size bh,bs,bv dữ liệu float64
        self.vec_3D = np.zeros((bh,bs,bv),dtype=np.float64) 
        
        #lấy chiều cao và rộng của ảnh
        he,wi = self.img.shape[:2] 

        # Duyệt từng pixel của ảnh
        for r in range(he):
            for c in range(wi):
                h,s,v = h_ch[r,c],s_ch[r,c],v_ch[r,c]

                i,j,k = int(h/180*bh),int(s/256*bs),int(v/256*bv)
                i,j,k = min(i,bh-1),min(j,bs-1),min(k,bv-1) #tránh vượt index

                self.vec_3D[i,j,k] += 1

        self.vec = self.vec_3D.flatten()

    def _normalize_vec_1D(self):
        #sum = sqrt(pixeli * pixeli) i = {0->n)
        tmp = 0.0
        for val in self.vec:
            tmp += val * val

        tmp = math.sqrt(tmp)
        if tmp != 0:
            self.vec /= tmp
