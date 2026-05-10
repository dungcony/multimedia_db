from models.mframe import MFrame
from models.mvideo import MVideo
from entities.frame import Frame
from entities.video import Video


@staticmethod
def model_to_entity(mframe: MFrame, video_id: int) -> Frame:
    return Frame(
        index=mframe.frame_idx,
        timesatmp_sec=mframe.timestamp_sec,
        vector=mframe.vec.tolist(),
        video_id=video_id
    )

@staticmethod
def model_to_entity(mvideo: MVideo) -> Video:
    return Video(
        cloudinary_url=mvideo.url,
        duration_sec=mvideo.duration_sec,
        frame_count=mvideo.frame_count,
        fps=mvideo.fps,
        height=mvideo.height,
        width=mvideo.width,
        file_size_bytes=mvideo.file_size_bytes,
    )