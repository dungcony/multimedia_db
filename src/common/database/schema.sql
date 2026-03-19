BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS videos (
    id BIGSERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT,
    codec TEXT,
    fps DOUBLE PRECISION NOT NULL CHECK (fps > 0),
    frame_count INTEGER NOT NULL CHECK (frame_count >= 0),
    duration_sec DOUBLE PRECISION NOT NULL CHECK (duration_sec >= 0),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shots (
    id BIGSERIAL PRIMARY KEY,
    video_id BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    shot_index INTEGER NOT NULL CHECK (shot_index >= 0),
    start_frame INTEGER NOT NULL CHECK (start_frame >= 0),
    end_frame INTEGER NOT NULL CHECK (end_frame >= start_frame),
    start_time_sec DOUBLE PRECISION NOT NULL CHECK (start_time_sec >= 0),
    end_time_sec DOUBLE PRECISION NOT NULL CHECK (end_time_sec >= start_time_sec),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (video_id, shot_index)
);

CREATE TABLE IF NOT EXISTS keyframes (
    id BIGSERIAL PRIMARY KEY,
    shot_id BIGINT NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL CHECK (frame_index >= 0),
    timestamp_sec DOUBLE PRECISION NOT NULL CHECK (timestamp_sec >= 0),
    image_path TEXT NOT NULL,
    is_representative BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (shot_id, frame_index)
);

CREATE TABLE IF NOT EXISTS features (
    id BIGSERIAL PRIMARY KEY,
    keyframe_id BIGINT NOT NULL REFERENCES keyframes(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    embedding VECTOR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (keyframe_id, model_name)
);

CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_shots_video_id ON shots(video_id);
CREATE INDEX IF NOT EXISTS idx_shots_time_range ON shots(video_id, start_time_sec, end_time_sec);
CREATE INDEX IF NOT EXISTS idx_keyframes_shot_id ON keyframes(shot_id);
CREATE INDEX IF NOT EXISTS idx_features_keyframe_id ON features(keyframe_id);

CREATE INDEX IF NOT EXISTS idx_features_embedding_cosine
ON features USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

COMMIT;
