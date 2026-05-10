import math

import cv2
import numpy as np


class RGB:
    def __init__(self,img):
        self.img = img
        self.img_f = img.astype(np.float64) # chuyển ảnh về float64 để tính toán chính xác hơn
        self.chanels = 3 #vì đầu vào luôn phải là anh màu RGB nên số kênh luôn là 3

    def to_gray_scale(self):
        r = self.img[:, :, 0].astype(np.float64)
        g = self.img[:, :, 1].astype(np.float64)
        b = self.img[:, :, 2].astype(np.float64)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        return gray
    
    def to_hsv(self):
        # lay chiều cao và rộng của ảnh
        he,wi = self.img.shape[:2]
        
        # lấy giá trị R, G, B của ảnh và chuyển về float64 để tính toán chính xác hơn
        r_ch, g_ch, b_ch = self.img_f[:,:,0]/255.0, self.img_f[:,:,1]/255.0, self.img_f[:,:,2]/255.0
        
        # tạo mảng 3 chiều có size he,wi,3 dữ liệu float64 để lưu giá trị HSV
        hsv = np.zeros((he,wi,3),dtype=np.float64)
        
        
        for h in range(he):
            for w in range(wi):
                r = r_ch[h,w]
                g = g_ch[h,w]
                b = b_ch[h,w]

                cmax = max(r,g,b)
                cmin = min(r,g,b)
                delta = cmax - cmin
                hue = 0
                
                if delta != 0:
                    if cmax == r:
                        hue = 60 * (((g - b) / delta) % 6)
                    elif cmax == g:
                        hue = 60 * ((b - r) / delta + 2)
                    else:
                        hue = 60 * ((r - g) / delta + 4)

                hue = hue / 2 # chia 2 để đưa về khoảng 0-179
                # Tính Saturation
                sat = (delta / cmax * 255) if cmax != 0 else 0

                # Tính Value
                val = cmax * 255

                hsv[h,w] = [hue, sat, val]

        return hsv

    def resize(self, wi,he):
        # dài rộng cũ
        o_h, o_w = self.img.shape[0], self.img.shape[1]
        
        # tạo ảnh mới có kích thước mới
        new_img = np.zeros((he, wi, self.chanels), dtype=np.float64)
        
        # tỷ lệ co giãn
        x_ratio = o_w / wi
        y_ratio = o_h / he
        
        for h in range(he):
            for w in range(wi):
                
                # tính vị trí tương ứng trên ảnh gốc
                x = (w+0.5) * x_ratio - 0.5
                y = (h+0.5) * y_ratio - 0.5
                
                # lấy 4 pixel lân cận
                x0 = max(int(math.floor(x)), 0)
                y0 = max(int(math.floor(y)), 0)
                x1 = min(x0 + 1, o_w - 1)
                y1 = min(y0 + 1, o_h - 1)
                
                # Tinh trọng số
                dx = max(x - math.floor(x), 0.0)
                dy = max(y - math.floor(y), 0.0)
                
                # nội suy bằng công thức 
                new_img[h,w] = (1 - dx) * (1 - dy) * self.img_f[y0, x0] 
                + dx * (1 - dy) * self.img_f[y0, x1] 
                + (1 - dx) * dy * self.img_f[y1, x0] 
                + dx * dy * self.img_f[y1, x1]
        
        #dùng hàm clip để đảm bảo giá trị pixel nằm trong khoảng 0-255 và chuyển về uint8
        return np.clip(new_img, 0, 255).astype(np.uint8)
    
    