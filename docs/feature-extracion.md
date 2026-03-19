# 🧠 BƯỚC 3: TRÍCH RÚT ĐẶC TRƯNG (FEATURE EXTRACTION)

## Quy trình thực hiện & Công nghệ sử dụng

---

## 📌 1. Mục tiêu

Sau khi đã có **Keyframe**, bước tiếp theo là:

* Chuyển ảnh (keyframe) → **vector số học (embedding)**
* Biểu diễn nội dung ảnh dưới dạng mà máy tính có thể so sánh
* Là nền tảng cho:

  * 🔍 Tìm kiếm tương đồng
  * 🤖 Hiểu nội dung ảnh/video

👉 Đây là **bước quan trọng nhất** quyết định độ “thông minh” của hệ thống.

---

## 📌 2. Tổng quan quy trình

```text id="q3k1v2"
Keyframe Input
    ↓
Tiền xử lý ảnh
    ↓
Feature Extraction (Handcrafted / Deep Learning)
    ↓
Sinh Vector (Embedding)
    ↓
Lưu vào PostgreSQL (pgvector)
```

---

## 📌 3. Ví dụ minh họa

### 🎨 Vector hóa ảnh (màu sắc)

**Ảnh đầu vào:** sân cỏ xanh

```text id="m8b7c1"
// Vector output (ví dụ)
[0.75, 0.05, 0.02, 0.05, 0.00, 0.00, 0.00, 0.13]
```

👉 Máy tính chỉ thấy:

* “75% là màu xanh”
* Không hiểu đó là **sân bóng, rừng hay tường sơn**

---

## 📌 4. Hai hướng tiếp cận chính

---

# ⚙️ 4.1. Đặc trưng truyền thống (Handcrafted Features)

---

## 🔹 Nguyên lý

* Sử dụng công thức toán học do con người thiết kế
* Trích xuất thông tin:

  * Màu sắc
  * Kết cấu (texture)
  * Hình dạng

---

## 🔹 Công nghệ sử dụng

* OpenCV
* scikit-image

---

## 🔹 Các kỹ thuật phổ biến

| Kỹ thuật      | Ý nghĩa          |
| ------------- | ---------------- |
| HSV Histogram | Phân bố màu      |
| LBP           | Texture          |
| HOG           | Hình dạng / cạnh |

---

## 🔹 Ví dụ (Histogram)

```python id="t7z2xp"
import cv2

def extract_histogram(image):
    hist = cv2.calcHist([image], [0,1,2], None, [8,8,8], [0,256]*3)
    hist = cv2.normalize(hist, hist).flatten()
    return hist
```

---

## 🔹 Đặc điểm

### 🟢 Ưu điểm

* Rất nhanh
* Vector nhỏ (~64–256 chiều)
* Tiết kiệm bộ nhớ
* Không cần GPU

---

### 🔴 Nhược điểm

#### ❗ Semantic Gap (Khoảng cách ngữ nghĩa)

* Hệ thống chỉ “thấy pixel”
* Không hiểu nội dung thực tế

👉 Ví dụ:

* Ảnh “biển” và “bầu trời” đều xanh → dễ bị nhầm

---

# 🚀 4.2. Deep Learning (Embedding ngữ nghĩa)

---

## 🔹 Nguyên lý

* Sử dụng mạng nơ-ron đã được train trên hàng triệu ảnh
* Học được:

  * Đối tượng (object)
  * Ngữ cảnh (context)
  * Hành động (action)

---

## 🔹 Công nghệ sử dụng

* PyTorch
* TensorFlow
* HuggingFace

---

## 🔹 Model phổ biến

| Model        | Đặc điểm        |
| ------------ | --------------- |
| ResNet       | Cân bằng tốt    |
| VGG          | Đơn giản        |
| EfficientNet | Tối ưu          |
| CLIP         | Hiểu ảnh + text |

---

## 🔹 Ví dụ (CLIP)

```python id="w6q2pk"
import torch
import clip
from PIL import Image

model, preprocess = clip.load("ViT-B/32")

def extract_clip_feature(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0)
    
    with torch.no_grad():
        feature = model.encode_image(image)
    
    return feature.numpy()[0]
```

---

## 🔹 Đặc điểm

### 🟢 Ưu điểm

* Hiểu nội dung ảnh rất tốt
* Tìm kiếm theo ngữ nghĩa
* Không phụ thuộc màu sắc

👉 Ví dụ:

* Tìm “con chó” → trả đúng dù ảnh sáng/tối khác nhau

---

### 🔴 Nhược điểm

* Vector lớn (512–2048 chiều)
* Tốn GPU khi trích xuất
* Cần DB hỗ trợ vector

---

## 📌 5. So sánh hai phương pháp

| Tiêu chí          | Handcrafted | Deep Learning |
| ----------------- | ----------- | ------------- |
| Tốc độ            | ⚡⚡⚡         | ⚡             |
| Độ chính xác      | ⭐⭐          | ⭐⭐⭐⭐          |
| Hiểu ngữ nghĩa    | ❌           | ✅             |
| Kích thước vector | Nhỏ         | Lớn           |
| GPU               | Không cần   | Nên có        |

---

## 📌 6. Lưu trữ vector trong PostgreSQL

---

### 🔸 Sử dụng pgvector

Cài extension:

```sql id="n8x4zp"
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 🔸 Thiết kế bảng

```sql id="zv2kda"
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    keyframe_id INT REFERENCES keyframes(id),
    embedding VECTOR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 🔸 Ý nghĩa

| Trường      | Mô tả            |
| ----------- | ---------------- |
| keyframe_id | Liên kết ảnh     |
| embedding   | Vector đặc trưng |

---

## 📌 7. Pipeline hoàn chỉnh

```text id="8x0vcz"
Keyframe
   ↓
Feature Extraction (CNN / CLIP)
   ↓
Vector (Embedding)
   ↓
PostgreSQL (pgvector)
   ↓
Similarity Search
```

---

## 📌 8. Best Practice

* Hệ thống nhỏ → dùng Handcrafted
* Hệ thống thực tế → dùng CLIP / ResNet
* Tối ưu:

  * Batch processing
  * Lưu cache vector
  * Dùng GPU

---

## 📌 9. Đánh giá

### ✅ Ưu điểm

* Biểu diễn dữ liệu hiệu quả
* Tăng độ chính xác tìm kiếm
* Cho phép search theo ngữ nghĩa

---

### ❌ Nhược điểm

* Tốn tài nguyên
* Cần tối ưu DB
* Vector lớn

---

## 📌 10. Hướng phát triển

* Fine-tune CLIP theo domain
* Multi-modal search (text + image)
* ANN search (FAISS / HNSW)
* Hybrid feature (color + deep learning)

---

## 📌 11. Kết luận

Feature Extraction là trái tim của hệ thống:

* Handcrafted → nhanh nhưng “ngu”
* Deep Learning → chậm hơn nhưng “hiểu”

👉 Trong thực tế:

> **Deep Learning (CLIP / CNN) là lựa chọn bắt buộc nếu muốn hệ thống thông minh**

---

✍️ *Gợi ý demo: cho cùng 1 query → so sánh kết quả giữa Histogram vs CLIP để thấy rõ sự khác biệt.*
