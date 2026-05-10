import uuid

from sqlalchemy import Float, Integer, ForeignKey, Uuid
from sqlalchemy.dialects.oracle import VECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Frame(Base):
    __tablename__ = "tbl_frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)  # Chỉ số của frame trong video
    timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False)  # Thời điểm của frame trong video (tính bằng giây)
    
    vector: Mapped[VECTOR] = mapped_column(VECTOR)

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("videos.id"),
        nullable=False,
    )

    video = relationship(
        "tbl_videos",
        back_populates="frames"
    )
