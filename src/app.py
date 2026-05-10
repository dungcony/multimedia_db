from services.feature import get_video


def upload_video():
    videos = get_video()
    evideos = []
    for i in videos:
        evideos.append(i.model_to_entity(videos[i]))
    
    