from ..entities.frame import Frame


class FrameRepo:
    def __init__(self, session):
        self.session = session

    def add_frame(self, frame):
        self.session.add(frame)
        self.session.commit()

    def get_frame_by_id(self, frame_id):
        return self.session.query(Frame).filter_by(id=frame_id).first()

    def get_frames_by_video_id(self, video_id):
        """Lấy tất cả frames thuộc 1 video, sắp xếp theo index."""
        return (
            self.session.query(Frame)
            .filter_by(video_id=video_id)
            .order_by(Frame.index)
            .all()
        )

    def update_frame(self, frame):
        self.session.merge(frame)
        self.session.commit()

    def delete_frame(self, frame):
        self.session.delete(frame)
        self.session.commit()