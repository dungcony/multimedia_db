import os
import cv2

# --- 1. Scan thư mục raw_videos để lấy danh sách video ---
RAW_VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '../public/raw_videos')
ACCEPTED_EXT = ['.mp4', '.mov', '.mkv']


def list_videos(video_dir=RAW_VIDEO_DIR):
    """Trả về danh sách file video hợp lệ."""
    videos = []
    for fname in os.listdir(video_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in ACCEPTED_EXT:
            videos.append(os.path.join(video_dir, fname))
    return videos

# --- 2. Đọc metadata video bằng OpenCV ---
def get_video_meta(video_path):
    """Đọc metadata video: fps, frame_count, duration, size."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_sec = frame_count / fps if fps > 0 else 0
    cap.release()
    return {
        'file_path': video_path,
        'file_name': os.path.basename(video_path),
        'fps': fps,
        'frame_count': frame_count,
        'duration_sec': duration_sec,
        'width': width,
        'height': height,
    }