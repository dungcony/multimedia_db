def insert_shots(shots, conn):
    """Insert danh sách shot vào bảng shots.
    
    Args:
        shots: list of dict, mỗi dict gồm:
            video_id, shot_index, start_frame, end_frame, start_time_sec, end_time_sec
        conn: psycopg2 connection
    """
    with conn.cursor() as cur:
        for s in shots:
            cur.execute(
                """
                INSERT INTO shots (video_id, shot_index, start_frame, end_frame, start_time_sec, end_time_sec)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (video_id, shot_index) DO NOTHING;
                """,
                (
                    s['video_id'],
                    s['shot_index'],
                    s['start_frame'],
                    s['end_frame'],
                    s['start_time_sec'],
                    s['end_time_sec'],
                )
            )
        conn.commit()


def update_video_status(video_id, status, conn, error_message=None):
    """Cập nhật status của video sau khi xử lý."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE videos SET status = %s, error_message = %s, updated_at = NOW()
            WHERE id = %s;
            """,
            (status, error_message, video_id)
        )
        conn.commit()
