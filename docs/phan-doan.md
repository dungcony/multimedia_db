# 🎬 HƯỚNG DẪN PHÂN ĐOẠN VIDEO (SHOT DETECTION)

## Quy trình thực hiện & Công nghệ sử dụng (PostgreSQL)

---

## 📌 1. Giới thiệu

Trong hệ thống tìm kiếm video, việc **phân đoạn video (Shot Detection)** là bước quan trọng nhằm:

* Chia video dài thành các đoạn nhỏ có nội dung đồng nhất
* Giảm chi phí xử lý đặc trưng
* Tăng độ chính xác khi tìm kiếm

Mỗi **shot** tương ứng với một cảnh liên tục, không bị gián đoạn bởi chuyển cảnh.

---

## 📌 2. Tổng quan quy trình

Quy trình phân đoạn video gồm các bước chính:

```text
Video Input 
   ↓
Frame Extraction
   ↓
Shot Detection (phát hiện chuyển cảnh)
   ↓
Xác định khoảng thời gian các shot
   ↓
Lưu metadata vào PostgreSQL
```

---

## 📌 3. Các bước thực hiện

---

### 🔹 Bước 1: Đọc và xử lý video

**Mục tiêu:**

* Đọc video đầu vào
* Lấy thông tin cơ bản:

  * FPS
  * Tổng số frame
  * Thời lượng

**Công nghệ sử dụng:**

* OpenCV (`cv2.VideoCapture`)

**Ý nghĩa:**

* Là cơ sở để tính toán thời gian và vị trí của từng shot

---

### 🔹 Bước 2: Trích xuất frame

**Mục tiêu:**

* Chuyển video thành chuỗi frame liên tiếp

**Cách thực hiện:**

* Đọc từng frame bằng OpenCV
* Hoặc dùng FFmpeg để trích frame theo tần suất (ví dụ: 1 FPS)

**Công nghệ:**

* OpenCV
* FFmpeg

**Ý nghĩa:**

* Frame là đơn vị cơ bản để so sánh và phát hiện thay đổi nội dung

---

### 🔹 Bước 3: Phát hiện chuyển cảnh (Shot Detection)

---

#### 📌 Phương pháp sử dụng: Histogram Difference

**Nguyên lý:**

* So sánh histogram màu giữa 2 frame liên tiếp
* Nếu độ khác biệt vượt ngưỡng → xác định là điểm chuyển cảnh

**Công thức:**

* Sử dụng Bhattacharyya Distance hoặc Chi-Square

---

#### 📌 Quy trình

1. Tính histogram cho mỗi frame
2. So sánh với frame trước
3. Nếu:

   ```text
   diff > threshold → cut
   ```

4. Ghi lại vị trí frame bắt đầu / kết thúc shot

---

#### 📌 Công nghệ sử dụng: OpenCV

**Ưu điểm:**

* Nhanh, chạy tốt trên CPU
* Dễ triển khai
* Phù hợp dataset lớn

**Nhược điểm:**

* Dễ bị nhiễu bởi:

  * Ánh sáng thay đổi đột ngột
  * Camera chuyển động (pan/zoom)
* Có thể sinh ra **false positive**

---

### 🔹 Bước 4: Xác định các đoạn shot

**Mục tiêu:**

* Từ các điểm cut → xác định khoảng:

  * start_frame
  * end_frame

**Chuyển đổi:**

* Frame → thời gian:

  ```text
  time = frame / fps
  ```

**Kết quả:**

* Danh sách các shot dạng:

  ```text
  (start_time, end_time)
  ```

---

### 🔹 Bước 5: (Tuỳ chọn) Cắt video thành từng shot

**Mục tiêu:**

* Tạo file video riêng cho mỗi shot

**Công nghệ:**

* FFmpeg

**Ý nghĩa:**

* Phục vụ bước trích đặc trưng hoặc demo trực quan

---

### 🔹 Bước 6: Lưu dữ liệu vào PostgreSQL

---

## 📌 4. Thiết kế cơ sở dữ liệu

---

### 🔸 Bảng `videos`

Lưu thông tin video gốc:

| Trường    | Ý nghĩa       |
| --------- | ------------- |
| id        | ID video      |
| file_path | Đường dẫn     |
| duration  | Thời lượng    |
| fps       | Số frame/giây |

---

### 🔸 Bảng `shots`

Lưu thông tin các đoạn video:

| Trường      | Ý nghĩa            |
| ----------- | ------------------ |
| id          | ID shot            |
| video_id    | Liên kết video     |
| start_time  | Thời gian bắt đầu  |
| end_time    | Thời gian kết thúc |
| start_frame | Frame bắt đầu      |
| end_frame   | Frame kết thúc     |
| shot_index  | Thứ tự shot        |

---

### 🔸 Quan hệ

```text
videos (1) —— (n) shots
```

---

### 🔸 Công nghệ sử dụng

* PostgreSQL
* psycopg2 (Python connector)

---

## 📌 5. Công nghệ đề xuất

---

### 🟢 1. OpenCV (Phương pháp truyền thống)

**Vai trò:**

* Đọc video
* Trích frame
* Tính histogram

**Đặc điểm:**

| Tiêu chí     | Đánh giá   |
| ------------ | ---------- |
| Tốc độ       | Rất nhanh  |
| Độ chính xác | Trung bình |
| Tài nguyên   | Thấp       |

---

### 🔵 2. PySceneDetect / AI Models (Khuyến nghị)

**Vai trò:**

* Phát hiện chuyển cảnh nâng cao

**Công nghệ:**

* Optical Flow
* 3D CNN

**Đặc điểm:**

| Tiêu chí     | Đánh giá             |
| ------------ | -------------------- |
| Tốc độ       | Chậm hơn             |
| Độ chính xác | Rất cao              |
| Tài nguyên   | Cao (có thể cần GPU) |

---

## 📌 6. So sánh hai phương pháp

| Tiêu chí | OpenCV | PySceneDetect |
| --- | --- | --- |
| Tốc độ | ⚡ Rất nhanh | 🐢 Chậm hơn |
| Độ chính xác | ⭐⭐ | ⭐⭐⭐⭐ |
| Dễ triển khai | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Phù hợp | Dataset lớn | Bài toán chính xác cao |

---

## 📌 7. Kết quả đầu ra

Sau khi xử lý, hệ thống thu được:

* Danh sách shot:

  ```text
  Shot 1: 0s → 5.2s
  Shot 2: 5.2s → 12.8s
  ...
  ```

* Metadata lưu trong PostgreSQL

* (Optional) File video cho từng shot

---

## 📌 8. Đánh giá & lưu ý

### ✅ Ưu điểm

* Giảm kích thước dữ liệu xử lý
* Tăng hiệu quả trích đặc trưng
* Dễ tích hợp vào hệ thống tìm kiếm

---

### ❌ Nhược điểm

* Phụ thuộc ngưỡng threshold
* Có thể sai với video nhiều chuyển động
* Cần tối ưu khi xử lý dataset lớn

---

## 📌 9. Hướng phát triển

* Sử dụng Deep Learning (Video Transformer)
* Adaptive threshold
* Kết hợp nhiều đặc trưng (color + motion)
* Lưu vector vào PostgreSQL (pgvector)

---

## 📌 10. Kết luận

Phân đoạn video là bước nền tảng trong hệ thống xử lý video, giúp:

* Tách nội dung thành các đơn vị có ý nghĩa
* Hỗ trợ mạnh cho tìm kiếm và phân tích video

Việc kết hợp:

* **OpenCV (nhanh)**
* **AI Models (chính xác)**
* **PostgreSQL (lưu trữ)**

sẽ tạo ra một hệ thống cân bằng giữa hiệu năng và độ chính xác.

---

✍️ *Gợi ý: Khi demo, nên hiển thị timeline video + vị trí các điểm cut đ*
