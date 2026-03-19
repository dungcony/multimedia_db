
# --- Lưu metadata vào DB (bảng videos) ---
def insert_video_meta(meta, conn):
    """Insert metadata vào bảng videos."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO videos (file_path, file_name, fps, frame_count, duration_sec, width, height, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (file_path) DO NOTHING;
            """,
            (
                meta['file_path'],
                meta['file_name'],
                meta['fps'],
                meta['frame_count'],
                meta['duration_sec'],
                meta['width'],
                meta['height'],
            )
        )
        conn.commit()

def get_video_pending(conn):
    """Get all pending videos."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM videos WHERE status = 'pending'
            """,
        )
        return cur.fetchall()