# BƯỚC 1 (SEGMENTS): ĐỌC VÀ XỬ LÝ VIDEO BẰNG OPENCV

## 1) Mục tiêu bước 1

Bước 1 chuẩn hóa đầu vào và đọc video để tạo dữ liệu nền cho các bước phát hiện shot:

- Đọc được metadata video: `fps`, `frame_count`, `duration`, `width`, `height`
- Chuẩn hóa định dạng kỹ thuật (nếu cần): codec, FPS, độ phân giải
- Sinh luồng frame ổn định để bước 2 (frame extraction) và bước 3 (shot detection) sử dụng

---

## 2) OpenCV: Input / Output / Config

### 2.1 Input

**Input chính:**

- `video_path`: đường dẫn file `.mp4`
- `video_id`: định danh video trong hệ thống
- (tuỳ chọn) `target_fps`, `target_width`, `target_height`

**Input cấu hình (`config`) đề xuất:**

```yaml
segment_step1:
 accepted_ext: [".mp4", ".mov", ".mkv"]
 min_duration_sec: 10
 target_fps: 25
 target_size: [224, 224]
 sample_fps_for_detection: 2
 use_ffmpeg_preprocess: true
 fail_on_corrupt_video: false
```

---

### 2.2 Output

**Output trong bộ nhớ (runtime):**

- `VideoMeta`:
 	- `video_id`
 	- `path`
 	- `fps`
 	- `frame_count`
 	- `duration_sec`
 	- `width`, `height`
- `FrameStream`: iterator/generator trả về `(frame_idx, timestamp_sec, frame_bgr)`

**Output lưu trữ (DB/log):**

- Bảng `videos` (hoặc record tương đương): metadata video sau khi kiểm tra/chuẩn hóa
- Log xử lý: video lỗi, video thiếu frame, video không đạt `min_duration_sec`

---

### 2.3 OpenCV config thực thi

```python
import cv2

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
  raise ValueError(f"Cannot open video: {video_path}")

fps = cap.get(cv2.CAP_PROP_FPS) or 0
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
duration_sec = frame_count / fps if fps > 0 else 0
```

**Lưu ý kỹ thuật:**

- OpenCV đọc frame theo màu **BGR** (không phải RGB)
- Cần kiểm tra `fps <= 0` để tránh lỗi chia 0
- Với video lỗi codec, ưu tiên tiền xử lý bằng FFmpeg rồi mới đưa vào OpenCV

---

## 3) Quy trình khuyến nghị cho bước 1

1. Validate input file (tồn tại, extension, dung lượng)
2. Mở video bằng `cv2.VideoCapture`
3. Trích metadata (`fps`, `frame_count`, `duration`, `size`)
4. Nếu lệch chuẩn (`fps/size/codec`) thì preprocess bằng FFmpeg
5. Tạo frame stream để cấp cho bước phát hiện chuyển cảnh
6. Lưu metadata + trạng thái xử lý vào DB

---

## 4) Công nghệ có thể sử dụng ở bước 1

### 4.1 Bắt buộc / cốt lõi

- **OpenCV (`cv2`)**
 	- Đọc video, lấy metadata, stream frame
 	- Phù hợp xử lý tuần tự theo frame trên CPU

### 4.2 Nên dùng kèm

- **FFmpeg / ffprobe**
 	- Chuẩn hóa codec/FPS/resolution trước khi OpenCV đọc
 	- Đọc metadata chính xác hơn với video đa dạng nguồn

- **NumPy**
 	- Xử lý ma trận frame, thống kê cơ bản, tiền xử lý nhanh

- **Pydantic hoặc dataclass**
 	- Chuẩn hóa schema `VideoMeta` và config runtime

### 4.3 Tầng lưu trữ & tích hợp

- **PostgreSQL + psycopg2 / SQLAlchemy**
 	- Lưu metadata bảng `videos`
 	- Gắn trạng thái xử lý (`pending`, `processed`, `failed`)

- **Logging (logging / structlog)**
 	- Truy vết video lỗi, thời gian xử lý, throughput

---

## 5) Mẫu API nội bộ đề xuất

```python
def load_video_meta(video_id: str, video_path: str, config: dict) -> dict:
  """Return validated and normalized metadata for one video."""

def iter_frames(video_path: str, stride: int = 1):
  """Yield (frame_idx, timestamp_sec, frame_bgr)."""
```

---

## 6) Best practice

- Tách rõ 2 lớp: **I/O video** và **phân tích shot**, tránh trộn logic
- Không giữ toàn bộ frame trong RAM; dùng generator để stream
- Chuẩn hóa đầu vào sớm (FPS/size/codec) để giảm lỗi dây chuyền ở bước sau
- Lưu metadata ngay sau khi đọc thành công để dễ resume pipeline
