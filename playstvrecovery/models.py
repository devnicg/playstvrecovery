from collections import deque
import http
import json
from operator import concat
import os
import time
from typing import Deque
from bs4 import BeautifulSoup
import bs4

import requests


class QueueWithRateLimit:
    """
    Rate Limiter
    """

    def __init__(self, max_requests: int, interval: int, delay: int) -> None:
        self.max_requests: int = max_requests
        self.interval: int = interval
        self.delay: int = delay
        self.queue: Deque = deque()

    def can_make_request(self) -> bool:
        current_time = time.time()
        while self.queue and self.queue[0] <= current_time - self.interval:
            self.queue.popleft()

        if len(self.queue) < self.max_requests:
            return True
        else:
            return False

    def request_with_retry(
        self, query: str, stream: bool | None = None
    ) -> requests.Response | None:
        while not self.can_make_request():
            print("Waiting for queue")
            time.sleep(self.delay)
        try:
            response = requests.get(query, stream=stream)
        except requests.exceptions.RequestException as ex:
            print(f"Failed GET request: {query}")
            print(ex)
            return
        else:
            return response


class Video:
    """
    Plays TV Video Object
    """

    def __init__(
        self,
        id: str,
        user: str,
        title: str,
        output_path: str,
        queue: QueueWithRateLimit,
    ) -> None:
        self.id: str = id
        self.user: str = user
        self.title: str = title
        self.output_path: str = output_path
        self.video_embeds_url: str = f"https://plays.tv/embeds/{self.id}"
        self.queue: QueueWithRateLimit = queue

    def download_video(self) -> None:
        file_name = concat(f"{self.user} - {self.title}", ".mp4")
        file_path = os.path.join(self.output_path, file_name)

        if os.path.isfile(file_path):
            print(f"{self.id} already exists on disk")
            return

        request_url = (
            f"https://web.archive.org/web/20191210043532/{self.video_embeds_url}"
        )

        response = self.queue.request_with_retry(request_url)

        if not response:
            print(f"Could not get archive for {self.id}")
            return

        page_content = BeautifulSoup(response.content, "html.parser")
        video_element = page_content.find("video")
        source_elements = video_element.find_all("source")

        if len(source_elements) < 1:
            print(f"Could not find source videos for {self.id}")
            return

        for i in range(len(source_elements)):
            try:
                source_element: bs4.Tag | bs4.NavigableString = source_elements[i]
                video_request_url = "https:" + source_element.attrs["src"]
                break
            except ValueError:
                continue

        if not video_request_url:
            print("No source video url was found in elements")
            return

        video_stream = self.queue.request_with_retry(video_request_url, stream=True)

        with open(file_path, "wb") as file:
            try:
                for chunk in video_stream.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
            except Exception as ex:
                print(ex)
                os.remove(file_path)
                print("Failed video download")


class UserProfile:
    """
    Plays TV User Profile
    """

    def __init__(
        self, username: str, output_path: str, queue: QueueWithRateLimit
    ) -> None:
        self.username: str = username
        self.output_path = output_path
        self.queue: QueueWithRateLimit = queue
        self.id: str
        self.videos: list[Video] = []

    def get_videos_from_profile(self) -> None:
        request_url = f"https://web.archive.org/web/20191210043532/https://plays.tv/u/{self.username}"

        response = self.queue.request_with_retry(request_url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")

            video_data = [
                json.loads(x.string)
                for x in soup.find_all("script", type="application/ld+json")
            ][0]["video"]

            try:
                self.id = soup.find("button", {"title": "Add Friend"}).attrs[
                    "data-obj-id"
                ]
            except ValueError:
                print("Could not get profile id")
                raise

            self.videos += [
                Video(
                    id=str(x["embedURL"]).split("/")[-1],
                    user=self.username,
                    output_path=self.output_path,
                    queue=self.queue,
                    title=" ".join(str(x["name"]).split("-")[1:]),
                )
                for x in video_data
            ]
        else:
            print("Failed to get initial profile")

    def get_more_videos_from_query(
        self, page_number: int = 1, previous_page_number: int = 0
    ) -> None:
        if page_number == previous_page_number:
            print("finished getting more videos")
            return

        next_page_number = page_number

        prepared_request = requests.PreparedRequest()
        request_base_url = (
            "https://web.archive.org/web/20191210164839/https://plays.tv/ws/module"
        )
        params = {
            "section": "videos",
            "page_num": page_number,
            "target_user_id": self.id,
            "infinite_scroll": True,
            "last_id": self.videos[-1].id,
            "custom_loading_module_state": "appending",
            "infinite_scroll_fire_only": True,
            "format": "application/json",
            "id": "UserVideosMod",
        }

        prepared_request.prepare_url(request_base_url, params)

        more_video_request = self.queue.request_with_retry(prepared_request.url)

        try:
            json_body = json.loads(more_video_request.text)
            body = json_body["body"]
        except ValueError:
            print("JSON decode failed!")

        if body and body != "":
            souped_body = BeautifulSoup(body, "html.parser")
            # Get video-items
            video_item_elements = souped_body.find_all("li", {"class": "video-item"})
            current_ids = [x.id for x in self.videos]
            video_list: list[Video] = []

            for video_item_element in video_item_elements:
                # if video_id does not exist on item, continue
                try:
                    video_id = video_item_element.attrs["data-feed-id"]
                except ValueError:
                    continue

                # if id not unique, continue
                if video_id in current_ids:
                    continue

                try:
                    title = video_item_element.find("a", {"class": "title"}).text
                except:
                    print(f"Failed to get title of video {video_id}")
                    continue
                video_list.append(
                    Video(
                        id=video_id,
                        user=self.username,
                        output_path=self.output_path,
                        queue=self.queue,
                        title=title,
                    )
                )
                current_ids.append(video_id)

            self.videos += video_list
            print(f"added {len(video_list)} to collection")
            next_page_number = page_number + 1
            pass

        self.get_more_videos_from_query(next_page_number, page_number)
