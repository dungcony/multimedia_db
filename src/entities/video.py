from time import timezone

from sqlalchemy import String, Float, Integer, BigInteger, Boolean, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid

from .base import Base


class Video(Base):
    __tablename__ = "tbl_videos"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Định danh & phân loại
    name: Mapped[str] = mapped_column(String, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)  # ID gốc từ nguồn (nếu có)
    species: Mapped[str] = mapped_column(String, nullable=True)

    # Lưu trữ
    cloudinary_url: Mapped[str] = mapped_column(String, nullable=False)

    # Thuộc tính kỹ thuật của video
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    frame_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Cờ tiền xử lý
    needs_resize: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    # Trạng thái pipeline (resume-friendly)
    keyframe_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    # Relationships
    frames = relationship("Frame", back_populates="video")