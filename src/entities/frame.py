import uuid

from sqlalchemy import Float, Integer, ForeignKey, Uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Frame(Base):
    __tablename__ = "tbl_frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False)

    vector = mapped_column(Vector(), nullable=True)

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tbl_videos.id"),
        nullable=False,
    )

    video = relationship(
        "Video",
        back_populates="frames"
    )
