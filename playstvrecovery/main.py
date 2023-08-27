import os
import time
import models


if __name__ == "__main__":
    user = models.UserProfile(
        username="rockettvc",
        output_path=os.path.join(os.getcwd(), "Downloads"),
        queue=models.QueueWithRateLimit(15, 60, 4),
    )
    print(f"getting profile for {user.username}")
    user.get_videos_from_profile()
    print(f"getting more videos for {user.username}")
    user.get_more_videos_from_query()
    print(f"starting downloads for {len(user.videos)} videos")
    for video in user.videos:
        print(f"Downloading - {video.id}")
        video.download_video()
