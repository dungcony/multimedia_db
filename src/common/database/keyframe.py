from dataclasses import dataclass
from typing import Optional

@dataclass
class Keyframe:
    id: Optional[int]
    shot_id: int
    frame_index: int
    timestamp_sec: float
    image_path: str
    is_representative: bool = True
    created_at: Optional[str] = None
