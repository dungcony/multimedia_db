"""Search service: tìm video tương đồng với ảnh đầu vào.

Flow:
  1. Nhận ảnh đầu vào (BGR numpy array hoặc file path)
  2. Trích xuất vector đặc trưng (Histogram + HOG)
  3. Lấy tất cả frames từ DB
  4. Tính cosine similarity giữa ảnh query và từng frame
  5. Gom nhóm theo video_id, giữ cosine similarity cao nhất
  6. Trả về top-K video có độ tương đồng cao nhất
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

from ..models.mframe import MFrame
from ..utils.cosin import cosine_distance
from ..repositories.conn import SessionLocal
from ..entities.frame import Frame
from ..entities.video import Video

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Cấu hình Histogram (HSV)
HIST_BINS = tuple(int(x) for x in os.getenv("HIST_BINS", "8,4,4").split(","))
HIST_RANGES = [int(x) for x in os.getenv("HIST_RANGES", "0,180,0,256,0,256").split(",")]

# Cấu hình HOG
HOG_BINS = int(os.getenv("HOG_BINS", 9))
HOG_CELL_SIZE = int(os.getenv("HOG_CELL_SIZE", 8))
HOG_BLOCK_SIZE = int(os.getenv("HOG_BLOCK_SIZE", 2))
HOG_RESIZE = (128, 128)

# Trọng số kết hợp vector
HIS_W = float(os.getenv("HIS_W", 0.5))
HOG_W = float(os.getenv("HOG_W", 0.5))


def extract_query_vector(image_bgr: np.ndarray) -> np.ndarray:
    """Trích xuất vector đặc trưng từ ảnh query.

    Args:
        image_bgr: Ảnh BGR numpy array (đọc từ cv2.imread hoặc upload).

    Returns:
        np.ndarray: Vector đặc trưng đã kết hợp Histogram + HOG.
    """
    mf = MFrame(
        frame=image_bgr,
        new_w=HOG_RESIZE[0],
        new_h=HOG_RESIZE[1],
        frame_idx=0,
        timestamp_sec=0.0,
    )
    mf.compute_his(HIST_BINS, HIST_RANGES)
    mf.compute_hog(HOG_BINS, HOG_CELL_SIZE, HOG_BLOCK_SIZE)
    mf.compute_vec(HIS_W, HOG_W)
    return mf.vec


def search_similar_videos(image_bgr: np.ndarray, top_k: int = 5) -> list[dict]:
    """Tìm top-K video tương đồng với ảnh query.

    Flow:
      1. Trích xuất vector đặc trưng từ ảnh
      2. Lấy tất cả frames + video info từ DB
      3. Tính cosine similarity cho từng frame
      4. Gom nhóm theo video_id:
         - Nếu video mới → thêm vào dict
         - Nếu video đã có mà cosine similarity cao hơn → cập nhật
      5. Sắp xếp và trả về top-K

    Args:
        image_bgr: Ảnh BGR numpy array.
        top_k: Số lượng video trả về (mặc định 5).

    Returns:
        list[dict]: Danh sách top-K video, mỗi item gồm:
            - video_id: UUID của video
            - similarity: Cosine similarity (0-1, càng cao càng giống)
            - video_url: URL của video trên Cloudinary
            - video_name: Tên video (nếu có)
            - duration_sec: Thời lượng video
            - frame_count: Số frame
            - keyframe_count: Số keyframe
    """
    # Bước 1: Trích xuất vector đặc trưng từ ảnh query
    query_vec = extract_query_vector(image_bgr)

    # Bước 2: Lấy tất cả frames từ DB kèm video info
    session = SessionLocal()
    try:
        frames = (
            session.query(Frame, Video)
            .join(Video, Frame.video_id == Video.id)
            .filter(Frame.vector.isnot(None))
            .all()
        )

        # Bước 3 & 4: Tính cosine similarity và gom nhóm theo video_id
        # Dict: {video_id: {"similarity": float, "video_info": Video}}
        video_scores: dict[str, dict] = {}

        for frame, video in frames:
            frame_vec = np.array(frame.vector, dtype=np.float64)

            # Cosine distance → Cosine similarity
            distance = cosine_distance(query_vec, frame_vec)
            similarity = 1.0 - distance  # distance = 1 - similarity

            video_id_str = str(video.id)

            if video_id_str not in video_scores:
                # Video mới → thêm vào dict
                video_scores[video_id_str] = {
                    "similarity": similarity,
                    "video": video,
                }
            else:
                # Video đã có → cập nhật nếu similarity cao hơn
                if similarity > video_scores[video_id_str]["similarity"]:
                    video_scores[video_id_str]["similarity"] = similarity

        # Bước 5: Sắp xếp theo similarity giảm dần, lấy top-K
        sorted_videos = sorted(
            video_scores.items(),
            key=lambda item: item[1]["similarity"],
            reverse=True,
        )[:top_k]

        # Định dạng kết quả trả về
        results = []
        for rank, (video_id, data) in enumerate(sorted_videos, 1):
            video = data["video"]
            results.append({
                "rank": rank,
                "video_id": video_id,
                "similarity": round(data["similarity"], 6),
                "video_url": video.cloudinary_url,
                "video_name": video.name or f"Video {video_id[:8]}",
                "duration_sec": video.duration_sec,
                "frame_count": video.frame_count,
                "keyframe_count": video.keyframe_count,
                "width": video.width,
                "height": video.height,
                "species": video.species,
            })

        return results

    finally:
        session.close()


def search_from_file(file_path: str, top_k: int = 5) -> list[dict]:
    """Tìm video tương đồng từ file ảnh.

    Args:
        file_path: Đường dẫn đến file ảnh.
        top_k: Số lượng video trả về.

    Returns:
        list[dict]: Kết quả tìm kiếm.
    """
    image_bgr = cv2.imread(file_path)
    if image_bgr is None:
        raise ValueError(f"Không thể đọc ảnh: {file_path}")
    return search_similar_videos(image_bgr, top_k)
