from ..entities.video import Video


class VideoRepo:
    def __init__(self, session):
        self.session = session

    def add_video(self, video):
        self.session.add(video)
        self.session.commit()
        return video

    def get_video_by_id(self, video_id):
        return self.session.query(Video).filter_by(id=video_id).first()

    def update_video(self, video):
        self.session.merge(video)
        self.session.commit()

    def delete_video(self, video):
        self.session.delete(video)
        self.session.commit()