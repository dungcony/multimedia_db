# 🖼️ BƯỚC 2: TRÍCH CHỌN KEYFRAME (KEYFRAME EXTRACTION)

## Quy trình thực hiện & Công nghệ sử dụng

---

## 📌 1. Mục tiêu

Sau khi đã phân đoạn video thành các **shot**, bước tiếp theo là:

* Chọn ra **1 hoặc vài frame đại diện (keyframe)** cho mỗi shot
* Giảm số lượng dữ liệu cần xử lý
* Tối ưu hóa lưu trữ và tăng tốc tìm kiếm

👉 Thay vì xử lý toàn bộ hàng nghìn frame, hệ thống chỉ cần làm việc với keyframe.

---

## 📌 2. Tổng quan quy trình

```text
Shot Input
   ↓
Trích xuất toàn bộ frame trong shot
   ↓
Áp dụng thuật toán chọn keyframe
   ↓
Lưu keyframe + metadata vào PostgreSQL
```

---

## 📌 3. Các phương pháp chọn Keyframe

---

### 🔹 Phương pháp 1: Middle Frame (Cơ bản)

**Ý tưởng:**

* Chọn frame ở giữa shot

**Cách tính:**

```text
middle_frame = (start_frame + end_frame) / 2
```

**Ưu điểm:**

* Rất nhanh
* Không cần tính toán phức tạp

**Nhược điểm:**

* Không đảm bảo đại diện tốt
* Có thể chọn trúng frame bị mờ

---

### 🔹 Phương pháp 2: I-Frame (FFmpeg)

---

#### 📌 Nguyên lý

* Video nén theo GOP (Group of Pictures)
* **I-frame** là frame chứa thông tin đầy đủ nhất
* FFmpeg có thể trích trực tiếp các frame này

---

#### 📌 Thực hiện

```bash
ffmpeg -i input.mp4 -vf "select=eq(pict_type\,I)" -vsync vfr keyframes_%03d.jpg
```

---

#### 📌 Đặc điểm

**🟢 Ưu điểm:**

* Tốc độ cực nhanh
* Không cần load toàn bộ video vào RAM
* Dễ tích hợp pipeline

**🔴 Nhược điểm:**

* Không dựa trên nội dung thực tế
* Có thể chọn frame:

  * Bị mờ (motion blur)
  * Không tiêu biểu

---

### 🔹 Phương pháp 3: Centroid Frame (K-Means Clustering)

---

#### 📌 Nguyên lý

1. Chuyển mỗi frame thành vector đặc trưng (pixel / CNN embedding)
2. Áp dụng K-Means clustering
3. Chọn frame gần **centroid** nhất

---

#### 📌 Quy trình

```text
Frames → Vector hóa → K-Means → Chọn Centroid Frame
```

---

#### 📌 Công nghệ sử dụng

* scikit-learn (`KMeans`)
* OpenCV / NumPy

---

#### 📌 Ví dụ code

```python
import cv2
import numpy as np
from sklearn.cluster import KMeans

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    return frames

def get_centroid_frame(frames, k=3):
    features = []
    
    for f in frames:
        resized = cv2.resize(f, (64, 64))
        features.append(resized.flatten())
    
    features = np.array(features)
    
    kmeans = KMeans(n_clusters=k, random_state=0).fit(features)
    
    centroid = kmeans.cluster_centers_[0]
    
    distances = np.linalg.norm(features - centroid, axis=1)
    idx = np.argmin(distances)
    
    return frames[idx]
```

---

#### 📌 Đặc điểm

**🟢 Ưu điểm:**

* Chọn frame đại diện tốt nhất
* Loại bỏ frame mờ / nhiễu
* Phản ánh nội dung thực tế

**🔴 Nhược điểm:**

* Tốn thời gian
* Tốn RAM
* Không phù hợp real-time

---

## 📌 4. So sánh các phương pháp

| Phương pháp    | Tốc độ | Độ chính xác | Tài nguyên | Khuyến nghị      |
| -------------- | ------ | ------------ | ---------- | ---------------- |
| Middle Frame   | ⚡⚡⚡    | ⭐⭐           | Thấp       | Demo nhanh       |
| FFmpeg I-frame | ⚡⚡⚡⚡   | ⭐⭐           | Rất thấp   | Production       |
| K-Means        | ⚡      | ⭐⭐⭐⭐         | Cao        | Độ chính xác cao |

---

## 📌 5. Lưu trữ Keyframe vào PostgreSQL

---

### 🔸 Thiết kế bảng `keyframes`

```sql
CREATE TABLE keyframes (
    id SERIAL PRIMARY KEY,
    shot_id INT REFERENCES shots(id),
    frame_index INT,
    image_path TEXT,
    feature_vector FLOAT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 🔸 Dữ liệu lưu trữ

| Trường         | Ý nghĩa          |
| -------------- | ---------------- |
| shot_id        | Liên kết shot    |
| frame_index    | Vị trí frame     |
| image_path     | Đường dẫn ảnh    |
| feature_vector | Vector đặc trưng |

---

### 🔸 Quy trình lưu

```text
Keyframe → Lưu ảnh → Trích feature → Lưu DB
```

---

## 📌 6. Pipeline hoàn chỉnh

```text
Video
 ↓
Shot Detection
 ↓
Keyframe Extraction
 ↓
Feature Extraction
 ↓
PostgreSQL Storage
```

---

## 📌 7. Best Practice

* Dataset nhỏ → dùng K-Means
* Dataset lớn → dùng FFmpeg
* Hybrid approach:

  * FFmpeg → lấy candidate frames
  * K-Means → refine

---

## 📌 8. Đánh giá

### ✅ Ưu điểm

* Giảm dữ liệu xử lý rất lớn
* Tăng tốc hệ thống tìm kiếm
* Dễ tích hợp pipeline AI

---

### ❌ Nhược điểm

* Có thể mất thông tin nếu chọn sai keyframe
* Trade-off giữa tốc độ và độ chính xác

---

## 📌 9. Hướng phát triển

* Dùng CLIP embedding thay vì pixel
* Attention-based keyframe selection
* Multi-keyframe per shot
* Lưu vector bằng pgvector

---

## 📌 10. Kết luận

Keyframe Extraction là bước quan trọng giúp:

* Đại diện hóa nội dung video
* Tối ưu tài nguyên hệ thống
* Tăng hiệu quả tìm kiếm

👉 Việc lựa chọn phương pháp phụ thuộc vào:

* Quy mô dữ liệu
* Tài nguyên phần cứng
* Yêu cầu độ chính xác

---

✍️ *Gợi ý demo: hiển thị mỗi shot + keyframe tương ứng để chứng minh tính đại diện.*
