from dataclasses import dataclass
from typing import Optional

@dataclass
class Video:
    id: Optional[int]
    external_id: Optional[str]
    file_path: str
    file_name: Optional[str]
    codec: Optional[str]
    fps: float
    frame_count: int
    duration_sec: float
    width: int
    height: int
    status: str = 'pending'
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
