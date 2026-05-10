CREATE TABLE videos (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Định danh & phân loại
    name              text NOT NULL,           -- vd "tiger_12345" hoặc "pixabay_tiger_12345"
    source_id         text,                    -- id gốc từ nguồn crawl (chỉ để debug, không unique)
    species           text NOT NULL,           -- nhãn loài → dùng evaluate precision/recall

    -- Lưu trữ
    cloudinary_url    text NOT NULL,

    -- Thuộc tính kỹ thuật của video
    fps               real,
    frame_count       integer,
    width             integer,
    height            integer,
    duration_sec      real,
    file_size_bytes   bigint,

    -- Cờ tiền xử lý
    needs_resize      boolean NOT NULL DEFAULT false,
                      -- 30 video có resolution lệch chuẩn (1366x720, 960x540...)
                      -- → batch job đọc cờ này để resize về 1280x720 trước khi extract

    -- Trạng thái pipeline (resume-friendly)
    keyframe_count    integer,                 -- NULL = chưa extract xong
    processed_at      timestamptz,             -- NULL = chưa xử lý

    created_at        timestamptz NOT NULL DEFAULT now()
);