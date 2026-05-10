# 📹 HỆ THỐNG CƠ SỞ DỮ LIỆU LƯU TRỮ VÀ TÌM KIẾM VIDEO

---

## 📌 1. Xây dựng bộ dữ liệu video

### 1.1. Yêu cầu

* Số lượng: **≥ 500 video**
* Độ dài mỗi video: **≥ 10 giây**
* Chủ đề thống nhất (ví dụ: thể thao, động vật, giao thông, vlog, game…)
* Định dạng: `.mp4` (H.264)

---

### 1.2. Nguồn dữ liệu

* Dataset công khai:

  * UCF101
  * Kinetics-400
  * HMDB51
* Hoặc thu thập từ:

  * YouTube
  * TikTok / các nguồn open data

---

### 1.3. Tiền xử lý dữ liệu

* Resize video về cùng kích thước (ví dụ: **224×224**)
* Chuẩn hóa FPS (ví dụ: **25 FPS**)
* Cắt video nếu quá dài
* Trích xuất frame:

```bash
ffmpeg -i input.mp4 -r 1 frames/frame_%04d.jpg
```

---

## 📌 2. Trích rút đặc trưng video

### 2.1. Mục tiêu

Chuyển mỗi video thành một vector đặc trưng để:

* So sánh nội dung
* Phục vụ tìm kiếm tương đồng

---

### 2.2. Các loại đặc trưng sử dụng

#### 🔹 (1) Đặc trưng hình ảnh (Visual Features)

* Model: ResNet50 / EfficientNet
* Input: frame ảnh
* Output: vector (512–2048 chiều)

**Giá trị:**

* Nhận diện vật thể, cảnh
* Phù hợp với truy vấn bằng ảnh

---

#### 🔹 (2) Đặc trưng chuyển động (Motion Features)

* Optical Flow
* 3D CNN (C3D, I3D)

**Giá trị:**

* Nhận diện hành động
* Phân biệt video có cùng cảnh nhưng khác chuyển động

---

#### 🔹 (3) Đặc trưng màu sắc (Color Features)

* Histogram RGB / HSV

**Giá trị:**

* Nhẹ, tính toán nhanh
* Phân biệt môi trường (biển, rừng, đô thị…)

---

#### 🔹 (4) Đặc trưng ngữ nghĩa (Semantic Features)

* Model: CLIP / Vision Transformer

**Giá trị:**

* Hiểu nội dung mức cao
* Kết nối ảnh và video (cross-modal)

---

### 2.3. Tổng hợp đặc trưng

Vector đặc trưng cuối:

```
Feature = [Visual | Motion | Color | Semantic]
```

Hoặc lấy trung bình các frame:

```
Video_feature = mean(frame_features)
```

---

## 📌 3. Xây dựng hệ thống tìm kiếm video

---

### 3.a. Sơ đồ khối hệ thống

```
        +------------------+
        |   Input Image    |
        +--------+---------+
                 |
                 v
        +------------------+
        | Feature Extractor|
        +--------+---------+
                 |
                 v
        +----------------------+
        | Feature Comparison   |
        +--------+-------------+
                 |
                 v
        +----------------------+
        |   Top-5 Video Output |
        +----------------------+
```

---

### 3.b. Quy trình thực hiện

#### 🔹 Bước 1: Trích rút đặc trưng video

* Trích frame từ video
* Đưa qua CNN / CLIP
* Lưu vector

---

#### 🔹 Bước 2: Lưu trữ cơ sở dữ liệu

Các lựa chọn:

* FAISS (khuyến nghị)
* PostgreSQL + vector extension
* Milvus / Pinecone

**Schema:**

```
Video_ID | Feature_Vector | Metadata
```

---

#### 🔹 Bước 3: Truy vấn bằng ảnh

* Input: ảnh
* Trích feature bằng model
* So sánh với vector video

---

#### 🔹 Bước 4: Tính độ tương đồng

Cosine Similarity:

```
sim(A, B) = (A · B) / (||A|| × ||B||)
```

---

#### 🔹 Bước 5: Trả kết quả

* Sắp xếp theo độ tương đồng giảm dần
* Lấy **Top-5 video**

---

### 3.c. Kết quả trung gian (ví dụ)

| Video         | Similarity |
| ------------- | ---------- |
| video_101.mp4 | 0.92       |
| video_233.mp4 | 0.88       |
| video_045.mp4 | 0.85       |
| video_399.mp4 | 0.83       |
| video_120.mp4 | 0.80       |

---

## 📌 4. Demo hệ thống

### 4.1. Công nghệ sử dụng

* Python
* OpenCV
* PyTorch / TensorFlow
* FAISS

---

### 4.2. Quy trình demo

```python
# Load model
model = load_clip()

# Extract feature từ ảnh
img_feature = model.encode_image(image)

# Tìm kiếm
results = faiss.search(img_feature, top_k=5)

# In kết quả
print(results)
```

---

## 📌 5. Đánh giá hệ thống

### 5.1. Tiêu chí đánh giá

* Precision@5
* Recall
* Thời gian truy vấn

---

### 5.2. Kết quả (ví dụ)

| Metric      | Value |
| ----------- | ----- |
| Precision@5 | 0.82  |
| Recall      | 0.76  |
| Query Time  | 0.15s |

---

### 5.3. Nhận xét

#### ✅ Ưu điểm

* Tìm kiếm nhanh
* Độ chính xác tốt
* Hỗ trợ ảnh chưa có trong dataset

#### ❌ Nhược điểm

* Phụ thuộc vào model
* Chưa hiểu ngữ cảnh sâu
* Tốn tài nguyên lưu trữ

---

## 📌 6. Hướng phát triển

* Áp dụng Video Transformer
* Tìm kiếm bằng text (text-to-video)
* Fine-tune theo domain
* Xây dựng web app (Flask / FastAPI)

---

## 📌 Kết luận

Hệ thống đã:

* Xây dựng bộ dữ liệu video ≥ 500 file
* Trích rút đặc trưng hiệu quả
* Thực hiện tìm kiếm video bằng ảnh với độ chính xác cao

---

✍️ **Ghi chú:** Có thể mở rộng thành hệ thống thực tế với giao diện web và API phục vụ tìm kiếm đa phương tiện.

- bài báo khoa học 
- 