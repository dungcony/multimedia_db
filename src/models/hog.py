import math
import numpy as np

from ..utils.l2nor import l2nor


class HOG:
    def __init__(self,img,bins,cell_size,block_size):
        self.img = img
        self.bins = bins
        self.cell_size = cell_size
        self.block_size = block_size    
        
        self.vec = None
        self.ang = None
        self.mag = None
        self.gx = None
        self.gy = None
        self.his_cell = None # mảng chứa histogram của từng cell
        
        self.compute()
        
    def compute(self):
        self._compute_gradients()
        self._compute_magnitude_angle()
        self._compute_cell_histogram()
        self._normalize_block_histogram()
        l2nor(self.vec)
        return self.vec

    # Tính gradient Gx và Gy cho từng pixel
    def _compute_gradients(self):
        he, wi = self.img.shape

        # tạo padding cho ảnh
        pad = np.zeros((he+2, wi+2), dtype=np.float64)
        pad[1:-1, 1:-1] = self.img # dán ảnh vào giữa

        self.gx = np.zeros((he,wi), dtype=np.float64)
        self.gy = np.zeros((he,wi), dtype=np.float64)

        for h in range(he):
            for w in range(wi):

                i = h + 1
                j = w + 1

                self.gx[h][w] = pad[i][j+1] - pad[i][j-1]
                self.gy[h][w] = pad[i-1][j] - pad[i+1][j]

    # Tính magnitude và angle cho từng pixel
    def _compute_magnitude_angle(self):
        he,wi = self.gx.shape
        self.mag = np.zeros((he,wi), dtype=np.float64)
        self.ang = np.zeros((he,wi), dtype=np.float64)

        for h in range(he):
            for w in range(wi):

                # magnitude = sqrt(Gx² + Gy²)
                self.mag[h][w] = math.sqrt(self.gx[h][w]**2 + self.gy[h][w]**2)

                # angle = arctan(Gy / Gx)
                self.ang[h][w] = math.degrees(math.atan2(self.gy[h][w],self.gx[h][w]))

                if self.ang[h][w] < 0:
                    self.ang[h][w] += 180

    # Tính histogram cho từng cell
    def _compute_cell_histogram(self):
        he,wi = self.mag.shape
        n_cell_h = he//self.cell_size # số lượng cell theo chiều cao
        n_cell_w = wi//self.cell_size # số lượng cell theo chiều rộng
        
        self.his_cell = np.zeros((n_cell_h,n_cell_w,self.bins), dtype=np.float64)
        
        for ci in range(n_cell_h):
            for cj in range(n_cell_w):
                # Duyệt từng cell
                for i in range(self.cell_size):
                    for j in range(self.cell_size):
                        # Duyệt dừng phần tử của cell  
                        # vị trí pixel thật trong ảnh           
                        pi =  ci * self.cell_size + i # self.cell_size
                        pj = cj * self.cell_size + j # self.cell_size

                        ang = self.ang[pi][pj]
                        mag = self.mag[pi][pj]

                        bin_idx = int(ang / 20)
                        bin_idx = min(bin_idx, self.bins - 1)
                        
                        self.his_cell[ci][cj][bin_idx] += mag
    
    # Chuẩn hóa histogram của block và tạo vector đặc trưng cuối cùng
    def _normalize_block_histogram(self):
        n_cell_h, n_cell_w, _ = self.his_cell.shape

        vec_block = []  # list chứa tất cả block đã chuẩn hóa

        # số block = (n_cell_h - block_size + 1) × (n_cell_w - block_size + 1)
        for ci in range(n_cell_h - self.block_size + 1):
            for cj in range(n_cell_w - self.block_size + 1):

                # Bước 1: Gộp tất cả cell trong block block_size × block_size
                his_bloc = []
                for i in range(self.block_size):
                    for j in range(self.block_size):
                        # ci+i, cj+j là vị trí cell thật trong his_cell
                        # ví dụ ci=0,cj=0,i=0,j=0 → cell A
                        #        ci=0,cj=0,i=0,j=1 → cell B
                        #        ci=0,cj=0,i=1,j=0 → cell E
                        #        ci=0,cj=0,i=1,j=1 → cell F
                        cell = self.his_cell[ci+i, cj+j, :]  # 9 số
                        for val in cell:
                            his_bloc.append(val)
                # his_bloc có block_size × block_size × bins số
                # block_size=2, bins=9 → 2×2×9 = 36 số

                # Bước 2: Chuẩn hóa L2 → triệt tiêu ảnh hưởng ánh sáng
                his_bloc = self._normal(np.array(his_bloc))

                # Bước 3: Thêm 36 số vào vec_block
                for val in his_bloc:
                    vec_block.append(val)

        # vec_block = tổng số block × 36 số
        # ví dụ ảnh 224×224, cell=8, block=2:
        # → 27×27×36 = 26244 chiều
        self.vec = np.array(vec_block)

    def _normal(self, vector):
        tmp = 0.0
        for val in vector:
            tmp += val * val
        tmp = math.sqrt(tmp)
        if tmp != 0:
            vector = vector / tmp
        return vector