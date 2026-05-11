import io
import os
import time
import tempfile

import numpy as np
import requests
import cv2

from dotenv import load_dotenv
load_dotenv()

from .mframe import MFrame
from .cnn import CNN


_cnn = None


def get_cnn():
    global _cnn
    if _cnn is None:
        _cnn = CNN()
    return _cnn


class MVideo:
    DOWNLOAD_TIMEOUT = 60
    DOWNLOAD_RETRIES = 3

    # Cấu hình Histogram (HSV)
    HIST_BINS = tuple(int(x) for x in os.getenv("HIST_BINS", "8,4,4").split(","))
    HIST_RANGES = [int(x) for x in os.getenv("HIST_RANGES", "0,180,0,256,0,256").split(",")]

    # Cấu hình HOG
    HOG_BINS = int(os.getenv("HOG_BINS", 9))
    HOG_CELL_SIZE = int(os.getenv("HOG_CELL_SIZE", 8))
    HOG_BLOCK_SIZE = int(os.getenv("HOG_BLOCK_SIZE", 2))
    HOG_RESIZE = (128, 128)

    # Cấu hình Texture (LBP + GLCM)
    TEXTURE_LBP_BINS = int(os.getenv("TEXTURE_LBP_BINS", 256))
    TEXTURE_GLCM_LEVELS = int(os.getenv("TEXTURE_GLCM_LEVELS", 8))
    TEXTURE_GLCM_DISTANCE = int(os.getenv("TEXTURE_GLCM_DISTANCE", 1))

    # Ngưỡng keyframe
    THRESHOLD = float(os.getenv("HIST_THRESHOLD", 0.6))

    # Trọng số kết hợp vector
    HIS_W = float(os.getenv("HIS_W", 0.5))
    HOG_W = float(os.getenv("HOG_W", 0.5))
    TEXT_W = float(os.getenv("TEXT_W", 0.5))

    def __init__(self, url, cnn=None):
        self.url = url
        self.mp4 = None
        self.frames = []
        self.fps = None
        self.frame_count = None
        self.width = None
        self.height = None
        self.duration_sec = None
        self.file_size_bytes = None
        self.cnn = cnn or get_cnn()

        self.download()
        self._get_key_frames_to_cnn(self.cnn)
        self.get_features()

    def download(self):
        last_error = None

        for attempt in range(1, self.DOWNLOAD_RETRIES + 1):
            try:
                response = requests.get(
                    self.url,
                    timeout=self.DOWNLOAD_TIMEOUT,
                    stream=True,
                )
                response.raise_for_status()

                buffer = io.BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    buffer.write(chunk)

                self.mp4 = buffer.getvalue()
                self.file_size_bytes = len(self.mp4)
                return self.mp4

            except requests.RequestException as e:
                last_error = e
                if attempt < self.DOWNLOAD_RETRIES:
                    time.sleep(attempt * 2)

        raise requests.RequestException(
            f"Tải video thất bại sau {self.DOWNLOAD_RETRIES} lần thử: {last_error}"
        )

    def get_features(self):
        self.file_size_bytes = len(self.mp4)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        try:
            os.write(tmp_fd, self.mp4)
            os.close(tmp_fd)

            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise ValueError(f"Không thể mở video: {tmp_path}")

            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if self.fps > 0:
                self.duration_sec = round(self.frame_count / self.fps, 3)

            cap.release()

            return {
                "fps": self.fps,
                "frame_count": self.frame_count,
                "width": self.width,
                "height": self.height,
                "duration_sec": self.duration_sec,
                "file_size_bytes": self.file_size_bytes,
            }

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    def _get_key_frames_to_cnn(self, cnn=None):
        cnn = cnn or self.cnn or get_cnn()
        thresh = self.THRESHOLD
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        cap = None
        
        try:
            os.write(tmp_fd, self.mp4)
            os.close(tmp_fd)

            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {tmp_path}")

            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if self.fps > 0:
                self.duration_sec = self.frame_count / self.fps

            keyframes = []
            prev_mframe = None
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp = round(frame_idx / self.fps, 3) if self.fps > 0 else 0.0
                mf = MFrame(
                    frame,
                    new_w=self.HOG_RESIZE[0],
                    new_h=self.HOG_RESIZE[1],
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp,
                )
                mf.compute_to_cnn(cnn)

                if prev_mframe is None:
                    is_keyframe = True
                else:
                    cosine = float(np.dot(prev_mframe.vec, mf.vec))
                    is_keyframe = cosine < thresh

                if is_keyframe:
                    keyframes.append(mf)
                    prev_mframe = mf

                frame_idx += 1

            self.frames = keyframes
            return keyframes
        finally:
            # Release cap TRUOC khi xoa file (tranh PermissionError tren Windows)
            if cap is not None:
                cap.release()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    def _get_key_frames(self):
        thresh = self.THRESHOLD
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        cap = None
        
        try:
            os.write(tmp_fd, self.mp4)
            os.close(tmp_fd)

            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {tmp_path}")

            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if self.fps > 0:
                self.duration_sec = self.frame_count / self.fps

            keyframes = []
            prev_mframe = None
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp = round(frame_idx / self.fps, 3) if self.fps > 0 else 0.0
                mf = MFrame(
                    frame,
                    new_w=self.HOG_RESIZE[0],
                    new_h=self.HOG_RESIZE[1],
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp,
                )
                mf.compute_his(self.HIST_BINS, self.HIST_RANGES)
                mf.compute_hog(self.HOG_BINS, self.HOG_CELL_SIZE, self.HOG_BLOCK_SIZE)
                mf.compute_texture(self.TEXTURE_LBP_BINS,self.TEXTURE_GLCM_LEVELS,self.TEXTURE_GLCM_DISTANCE,)
                mf.compute_vec(self.HIS_W, self.HOG_W, self.TEXT_W)

                if prev_mframe is None:
                    is_keyframe = True
                else:
                    cosine = float(np.dot(prev_mframe.vec, mf.vec))
                    is_keyframe = cosine < thresh

                if is_keyframe:
                    keyframes.append(mf)
                    prev_mframe = mf

                frame_idx += 1

            self.frames = keyframes
            return keyframes

        finally:
            # Release cap TRUOC khi xoa file (tranh PermissionError tren Windows)
            if cap is not None:
                cap.release()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


    def model_to_entity(self):
        """Chuyển MVideo model → Video entity (SQLAlchemy ORM)."""
        from ..entities.video import Video

        return Video(
            cloudinary_url=self.url,
            fps=self.fps,
            frame_count=self.frame_count,
            width=self.width,
            height=self.height,
            duration_sec=self.duration_sec,
            file_size_bytes=self.file_size_bytes,
            keyframe_count=len(self.frames),
        )

    def frames_to_entities(self, video_id):
        """Chuyển danh sách MFrame → list Frame entities."""
        from ..entities.frame import Frame

        entities = []
        for mf in self.frames:
            entities.append(Frame(
                index=mf.frame_idx,
                timestamp_sec=mf.timestamp_sec,
                vector=mf.vec.tolist() if mf.vec is not None else None,
                video_id=video_id,
            ))
        return entities
