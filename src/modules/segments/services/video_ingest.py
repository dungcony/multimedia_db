import cv2
import os
from src.common.database.conn import get_conn
from src.common.services.get_video import list_videos, get_video_meta

from src.modules.segments.models import Video
from src.modules.segments.repositories import insert_video_meta

# --- Pipeline tổng hợp ---
def ingest_all_videos():
    """Scan, đọc metadata, lưu DB cho tất cả video trong raw_videos."""
    # Kết nối DB qua conn.py
    conn = get_conn()
    video_paths = list_videos() # Lấy danh sách video
    for vpath in video_paths:
        try:
            meta = get_video_meta(vpath)
            insert_video_meta(meta, conn)
            print(f"Đã lưu: {meta['file_name']}")
        except Exception as e:
            print(f"Lỗi với {vpath}: {e}")
    conn.close()

if __name__ == '__main__':
    ingest_all_videos()
