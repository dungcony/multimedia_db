"""Search service: tìm video tương đồng với ảnh đầu vào bằng CNN.

Flow:
  1. Nhận ảnh đầu vào (BGR numpy array hoặc file path)
  2. Trích xuất vector CNN
  3. Lấy tất cả frames từ DB
  4. Tính cosine similarity giữa ảnh query và từng frame
  5. Gom nhóm theo video_id, giữ cosine similarity cao nhất
  6. Trả về top-K video có độ tương đồng cao nhất
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

from ..models.cnn import CNN
from ..repositories.conn import SessionLocal
from ..entities.frame import Frame
from ..entities.video import Video

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _normalize_vec(vec: np.ndarray) -> np.ndarray:
	norm = np.linalg.norm(vec)
	if norm > 1e-10:
		return vec / norm
	return vec


def extract_query_vector(image_bgr: np.ndarray, cnn: CNN) -> np.ndarray:
	"""Trích xuất vector CNN từ ảnh query (BGR)."""
	if image_bgr is None:
		raise ValueError("Ảnh đầu vào rỗng (None)")
	vec = cnn.extract(image_bgr)
	return _normalize_vec(vec)


def search_similar_videos(
	image_bgr: np.ndarray,
	top_k: int = 5,
	cnn: CNN | None = None,
) -> list[dict]:
	"""Tìm top-K video tương đồng với ảnh query bằng CNN."""
	if cnn is None:
		cnn = CNN()

	query_vec = extract_query_vector(image_bgr, cnn)

	session = SessionLocal()
	try:
		frames = (
			session.query(Frame, Video)
			.join(Video, Frame.video_id == Video.id)
			.filter(Frame.vector.isnot(None))
			.all()
		)

		video_scores: dict[str, dict] = {}

		for frame, video in frames:
			if frame.vector is None:
				continue

			frame_vec = np.asarray(frame.vector, dtype=np.float32)
			if frame_vec.ndim != 1 or frame_vec.size == 0:
				continue

			frame_vec = _normalize_vec(frame_vec)
			similarity = float(np.dot(query_vec, frame_vec))

			video_id_str = str(video.id)
			if video_id_str not in video_scores:
				video_scores[video_id_str] = {
					"similarity": similarity,
					"video": video,
				}
			else:
				if similarity > video_scores[video_id_str]["similarity"]:
					video_scores[video_id_str]["similarity"] = similarity

		sorted_videos = sorted(
			video_scores.items(),
			key=lambda item: item[1]["similarity"],
			reverse=True,
		)[:top_k]

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


def search_from_file(
	file_path: str,
	top_k: int = 5,
	cnn: CNN | None = None,
) -> list[dict]:
	"""Tìm video tương đồng từ file ảnh."""
	image_bgr = cv2.imread(file_path)
	if image_bgr is None:
		raise ValueError(f"Không thể đọc ảnh: {file_path}")
	return search_similar_videos(image_bgr, top_k, cnn)
