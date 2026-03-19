# Database Schema

Hệ thống sử dụng **PostgreSQL** kết hợp **pgvector** để lưu trữ metadata video, phân đoạn (shot), keyframe và vector đặc trưng phục vụ tìm kiếm tương tự.

## Sơ đồ quan hệ

```
videos (1) ──< (N) shots (1) ──< (N) keyframes (1) ──< (N) features
```

Một video có nhiều shot, mỗi shot có nhiều keyframe, mỗi keyframe có nhiều feature vector (tương ứng với các model trích xuất khác nhau).

---

## 1. Bảng `videos`

Lưu metadata của từng video gốc trong thư mục `raw_videos`.

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|--------|------|-----------|---------|
| `id` | BIGSERIAL | PRIMARY KEY | Khóa chính, tự tăng |
| `external_id` | TEXT | UNIQUE | ID từ nguồn bên ngoài (VD: YouTube ID), dùng khi video được lấy từ hệ thống khác |
| `file_path` | TEXT | NOT NULL, UNIQUE | Đường dẫn đầy đủ tới file video, unique để tránh nhập trùng |
| `file_name` | TEXT | | Tên file (VD: `lion_30088597.mp4`) |
| `codec` | TEXT | | Codec video (VD: `h264`, `hevc`) |
| `fps` | DOUBLE PRECISION | NOT NULL, > 0 | Số frame trên giây |
| `frame_count` | INTEGER | NOT NULL, >= 0 | Tổng số frame trong video |
| `duration_sec` | DOUBLE PRECISION | NOT NULL, >= 0 | Thời lượng video (giây) |
| `width` | INTEGER | NOT NULL, > 0 | Chiều rộng (pixel) |
| `height` | INTEGER | NOT NULL, > 0 | Chiều cao (pixel) |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | Trạng thái xử lý: `pending` (chờ xử lý), `processed` (đã xong), `failed` (lỗi) |
| `error_message` | TEXT | | Thông báo lỗi nếu xử lý thất bại |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm tạo bản ghi |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm cập nhật lần cuối |

**Index:**
- `idx_videos_status` — Tìm nhanh video theo trạng thái (VD: lấy tất cả video `pending` để xử lý tiếp)

---

## 2. Bảng `shots`

Lưu các phân đoạn (shot) được tách ra từ mỗi video bằng thuật toán shot detection (histogram diff, PySceneDetect...).

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|--------|------|-----------|---------|
| `id` | BIGSERIAL | PRIMARY KEY | Khóa chính, tự tăng |
| `video_id` | BIGINT | NOT NULL, FK → videos(id), ON DELETE CASCADE | Video chứa shot này, xóa video sẽ xóa luôn các shot |
| `shot_index` | INTEGER | NOT NULL, >= 0 | Thứ tự shot trong video (bắt đầu từ 0) |
| `start_frame` | INTEGER | NOT NULL, >= 0 | Frame bắt đầu của shot |
| `end_frame` | INTEGER | NOT NULL, >= start_frame | Frame kết thúc của shot |
| `start_time_sec` | DOUBLE PRECISION | NOT NULL, >= 0 | Thời điểm bắt đầu (giây) |
| `end_time_sec` | DOUBLE PRECISION | NOT NULL, >= start_time_sec | Thời điểm kết thúc (giây) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm tạo bản ghi |

**Ràng buộc:** `UNIQUE (video_id, shot_index)` — mỗi video không có 2 shot trùng thứ tự.

**Index:**
- `idx_shots_video_id` — Tìm nhanh tất cả shot của một video
- `idx_shots_time_range` — Tìm shot theo khoảng thời gian trong video

---

## 3. Bảng `keyframes`

Lưu các frame đại diện được trích xuất từ mỗi shot (VD: frame giữa, I-frame, hoặc chọn bằng K-Means).

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|--------|------|-----------|---------|
| `id` | BIGSERIAL | PRIMARY KEY | Khóa chính, tự tăng |
| `shot_id` | BIGINT | NOT NULL, FK → shots(id), ON DELETE CASCADE | Shot chứa keyframe này |
| `frame_index` | INTEGER | NOT NULL, >= 0 | Vị trí frame trong video gốc |
| `timestamp_sec` | DOUBLE PRECISION | NOT NULL, >= 0 | Thời điểm của frame (giây) |
| `image_path` | TEXT | NOT NULL | Đường dẫn tới ảnh keyframe đã lưu trên disk |
| `is_representative` | BOOLEAN | NOT NULL, DEFAULT TRUE | Đánh dấu keyframe đại diện chính của shot (dùng cho hiển thị/tìm kiếm) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm tạo bản ghi |

**Ràng buộc:** `UNIQUE (shot_id, frame_index)` — mỗi shot không lưu trùng frame.

**Index:**
- `idx_keyframes_shot_id` — Tìm nhanh tất cả keyframe của một shot

---

## 4. Bảng `features`

Lưu vector đặc trưng (embedding) của mỗi keyframe, phục vụ tìm kiếm video tương tự bằng cosine similarity.

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|--------|------|-----------|---------|
| `id` | BIGSERIAL | PRIMARY KEY | Khóa chính, tự tăng |
| `keyframe_id` | BIGINT | NOT NULL, FK → keyframes(id), ON DELETE CASCADE | Keyframe tương ứng |
| `model_name` | TEXT | NOT NULL | Tên model đã dùng để trích xuất (VD: `resnet50`, `clip-vit-b32`) |
| `embedding` | VECTOR(512) | NOT NULL | Vector đặc trưng 512 chiều (pgvector) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm tạo bản ghi |

**Ràng buộc:** `UNIQUE (keyframe_id, model_name)` — mỗi keyframe chỉ có 1 embedding cho mỗi model.

**Index:**
- `idx_features_keyframe_id` — Tìm nhanh feature theo keyframe
- `idx_features_embedding_cosine` — **IVFFlat index** (100 lists) trên cột `embedding` với `vector_cosine_ops`, tăng tốc truy vấn tìm kiếm tương tự (approximate nearest neighbor)

---

## Luồng dữ liệu

```
Video file (.mp4)
    │
    ▼
[1] Ingest → bảng videos (metadata: fps, duration, size...)
    │
    ▼
[2] Shot Detection → bảng shots (phân đoạn theo cảnh)
    │
    ▼
[3] Keyframe Extraction → bảng keyframes (frame đại diện + ảnh trên disk)
    │
    ▼
[4] Feature Extraction → bảng features (embedding vector 512D)
    │
    ▼
[5] Search → cosine similarity trên bảng features → trả về keyframe/shot/video
```
