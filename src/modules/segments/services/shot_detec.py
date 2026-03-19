import cv2
import numpy as np
from src.common.database.conn import get_conn
from src.modules.segments.repositories.video_repo import get_video_pending
from src.modules.segments.repositories.shot_repo import insert_shots, update_video_status


def compute_histogram(frame):
    """Tính histogram HSV chuẩn hóa cho 1 frame."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return hist


def detect_shots(video_path, threshold=0.6):
    """Phát hiện chuyển cảnh bằng Bhattacharyya distance trên histogram HSV.
    
    Args:
        video_path: đường dẫn file video
        threshold: ngưỡng Bhattacharyya distance, vượt qua = chuyển cảnh
        
    Returns:
        list of (start_frame, end_frame) cho từng shot
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    ret, prev_frame = cap.read()
    if not ret:
        cap.release()
        return []

    prev_hist = compute_histogram(prev_frame)
    cut_points = [0]
    frame_idx = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        curr_hist = compute_histogram(frame)
        dist = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_BHATTACHARYYA)

        if dist > threshold:
            cut_points.append(frame_idx)

        prev_hist = curr_hist
        frame_idx += 1

    cap.release()

    # Tạo danh sách shot từ cut points
    shots = []
    for i in range(len(cut_points)):
        start = cut_points[i]
        end = cut_points[i + 1] - 1 if i + 1 < len(cut_points) else total_frames - 1
        shots.append({
            'shot_index': i,
            'start_frame': start,
            'end_frame': end,
            'start_time_sec': round(start / fps, 3),
            'end_time_sec': round(end / fps, 3),
        })

    return shots


def process_all_pending(threshold=0.6):
    """Lấy tất cả video pending, detect shot, lưu DB."""
    conn = get_conn()
    rows = get_video_pending(conn)

    if not rows:
        print("Không có video pending nào.")
        conn.close()
        return

    print(f"Tìm thấy {len(rows)} video pending.")

    for row in rows:
        video_id = row[0]
        file_path = row[2]
        file_name = row[3]

        try:
            print(f"Đang xử lý: {file_name}...", end=" ")
            shots = detect_shots(file_path, threshold)

            for s in shots:
                s['video_id'] = video_id

            insert_shots(shots, conn)
            update_video_status(video_id, 'processed', conn)
            print(f"OK — {len(shots)} shots")

        except Exception as e:
            update_video_status(video_id, 'failed', conn, str(e))
            print(f"LỖI — {e}")

    conn.close()
    print("Hoàn tất.")


if __name__ == '__main__':
    process_all_pending()
