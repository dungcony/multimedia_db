from dataclasses import dataclass
from typing import Optional

@dataclass
class Shot:
    id: Optional[int]
    video_id: int
    shot_index: int
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float
    created_at: Optional[str] = None
