from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Feature:
    id: Optional[int]
    keyframe_id: int
    model_name: str
    embedding: List[float]
    created_at: Optional[str] = None
