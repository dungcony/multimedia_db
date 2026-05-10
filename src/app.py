import time

from .services.feature import get_video
from .repositories.conn import SessionLocal, engine
from .repositories.video_repo import VideoRepo
from .repositories.frame_repo import FrameRepo
from .entities.base import Base


def create_tables():
    """Create all tables if not exist."""
    Base.metadata.create_all(bind=engine)


def upload_videos():
    """Flow: download videos -> extract keyframes -> save to DB."""

    # Step 0: Create tables
    print("=" * 60)
    print("[STEP 0] Creating tables if not exist...")
    create_tables()
    print("[STEP 0] Done.")

    # Step 1: Read CSV + download + extract keyframes
    print("=" * 60)
    print("[STEP 1] Loading videos from CSV...")
    t0 = time.time()
    mvideos = get_video()
    t1 = time.time()
    print(f"[STEP 1] Loaded {len(mvideos)} videos in {t1 - t0:.1f}s")

    # Step 2: Save to DB
    print("=" * 60)
    print("[STEP 2] Saving to database...")
    session = SessionLocal()
    video_repo = VideoRepo(session)
    frame_repo = FrameRepo(session)

    saved_count = 0
    total_frames = 0

    try:
        for i, mvideo in enumerate(mvideos, 1):
            t_start = time.time()

            # Save Video entity
            video_entity = mvideo.model_to_entity()
            video_repo.add_video(video_entity)

            # Save Frame entities
            frame_entities = mvideo.frames_to_entities(video_entity.id)
            for frame_entity in frame_entities:
                frame_repo.add_frame(frame_entity)

            t_end = time.time()
            n_frames = len(mvideo.frames)
            total_frames += n_frames
            saved_count += 1

            print(
                f"  [{i}/{len(mvideos)}] "
                f"keyframes={n_frames}, "
                f"fps={mvideo.fps:.1f}, "
                f"size={mvideo.file_size_bytes // 1024}KB, "
                f"save_time={t_end - t_start:.1f}s"
            )

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed at video {saved_count + 1}: {e}")
        raise
    finally:
        session.close()

    print("=" * 60)
    print(f"[DONE] Saved {saved_count} videos, {total_frames} keyframes total.")


if __name__ == "__main__":
    upload_videos()