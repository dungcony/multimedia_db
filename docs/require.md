# 📹 HỆ THỐNG CƠ SỞ DỮ LIỆU LƯU TRỮ VÀ TÌM KIẾM VIDEO

## 1. Xây dựng bộ dữ liệu video

### 1.1 Mô tả

- Thu thập **≥ 500 video**
- Độ dài mỗi video: **≥ 10 giây**
- Chủ đề: *(ví dụ)* thể thao / động vật / giao thông / vlog / gaming
- Định dạng: `.mp4` (H.264, phổ biến, dễ xử lý)

### 1.2 Nguồn dữ liệu

- YouTube (sử dụng API hoặc tool tải video)
- Dataset công khai:
  - UCF101
  - Kinetics-400
  - HMDB51

### 1.3 Tiền xử lý

- Resize video về cùng kích thước (ví dụ: 224x224)
- Chuẩn hóa FPS (ví dụ: 25 FPS)
- Cắt clip nếu quá dài
- Trích frame:

  ```bash
  ffmpeg -i input.mp4 -r 1 frames/frame_%04d.jpg
