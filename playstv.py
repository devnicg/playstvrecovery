from asyncio.proactor_events import _ProactorBasePipeTransport
from datetime import datetime
from genericpath import isfile
import json
from operator import concat
import os
from pathlib import Path
from time import sleep
from typing import Annotated, Callable, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
from requests.models import PreparedRequest
import typer
from rich import print
from rich.progress import track

from waybackpy import WaybackMachineAvailabilityAPI
from waybackpy.exceptions import ArchiveNotInAvailabilityAPIResponse


class Video:
    def __init__(self, id: str, title: str, description: str) -> None:
        self.id: str = id
        self.valid: bool = False
        self.title: str = title
        self.video_url: str
        self.video_resolution: int
        self.description: str = description
        self.original_url: str = f"https://plays.tv/embeds/{self.id}"
        self.archive_url: str = str()
        self.__archive_date__: datetime = datetime(year=2019, month=12, day=10, hour=17)
        self.__wayback_user_agent__: str = str(
            "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        )

    def download_video(self, output_path: str) -> None:
        try:
            archive_page = requests.get(self.archive_url)
        except:
            structured_error(
                "download", f"Failed to get archive url content for {self.title}"
            )

        archive_page_content = BeautifulSoup(archive_page.content, "html.parser")

        try:
            video_element = archive_page_content.find("video")
        except:
            structured_error(
                "download", f"Could not find video element for {self.title}"
            )
            sleep(2)
            return

        try:
            source_elements = video_element.find_all("source")

            if len(source_elements) < 1:
                structured_error(
                    "download", f"Could not find source element for {self.title}"
                )

                sleep(2)
                return

            for i in range(len(source_elements)):
                source_element: Tag | NavigableString = source_elements[i]
                self.video_url = "https:" + source_element.attrs["src"]
                self.video_resolution = source_element.attrs["res"]
                break
        except:
            structured_error(
                "download", f"Could not find source element for {self.title}"
            )
            sleep(2)
            return

        try:
            structured_info("download", f"Starting download")
            file_name = concat(self.title, ".mp4")
            file_path = os.path.join(output_path, file_name)

            if os.path.isfile(file_path):
                structured_info("download", f"Download of {self.title} already exists!")
                return

            video_stream = requests.get(self.video_url, stream=True)

            with open(file_path, "wb") as file:
                for chunk in video_stream.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

            structured_info(
                "download", f"[green]Successfully[/green] downloaded {self.title}"
            )

        except:
            structured_error("download", f"Failed to download {self.title}")
            sleep(2)
            return

    def check_availability(self) -> bool:
        structured_info("availability", f"Checking {self.title}")
        availability_api = WaybackMachineAvailabilityAPI(
            self.original_url, self.__wayback_user_agent__
        )

        possible_url = availability_api.near(
            year=self.__archive_date__.year,
            month=self.__archive_date__.month,
            day=self.__archive_date__.day,
            hour=self.__archive_date__.hour,
        )

        if possible_url is None:
            return False

        try:
            self.archive_url = possible_url.archive_url
        except ArchiveNotInAvailabilityAPIResponse as ex:
            self.valid = False
            return False
        else:
            self.valid = True
            return True


class UserProfile:
    def __init__(self, username: str) -> None:
        self.username: str = username
        self.video_ids: [str] = []
        self.videos: [Video] = []
        self.original_url: str = str(f"https://plays.tv/u/{self.username}")
        self.archive_url: str = str()
        self.__user_id__: str = str()
        self.__module_url__: str = "https://plays.tv/ws/module"
        self.__last_video_fetched__: bool = False
        self.__last_video_id__: str = str()
        self.__archive_video_data__: [] = []
        self.__current_page_number__: int = 0
        self.__wayback_user_agent__: str = str(
            "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        )
        self.__archive_date__: datetime = datetime(year=2019, month=12, day=10)

    def __str__(self) -> str:
        return f"---------\nUsername: {self.username} \nPossible videos: {len(self.video_ids)} \nActual Videos {len(self.videos)} \n---------"

    def get_id_from_url(url: str) -> str:
        pass

    def get_user_id(self) -> None:
        try:
            content = requests.get(self.archive_url).content
            soup = BeautifulSoup(content, "html.parser")
            html_element = soup.find("button", {"title": "Add Friend"})

            if html_element is not None:
                self.__user_id__ = html_element.attrs["data-obj-id"]
                structured_info(
                    "initialization", f"Retrieved user id ({self.__user_id__})"
                )
        except:
            structured_error("initialization", "Failed to retrieve user id")

    def check_video_availability(self) -> None:
        for vid_index in track(
            range(len(self.videos)), description="Checking video availability..."
        ):
            current_vid: Video = self.videos[vid_index]
            current_vid.check_availability()

    def get_more_videos(self) -> list[Video] | None:
        if self.__last_video_fetched__:
            self.check_video_availability()
            return
        video_list: list[Video] = []

        params = {
            "infinite_scroll": True,
            "infinite_scroll_fire_only": True,
            "custom_loading_module_state": "appending",
            "page_num": self.__current_page_number__ + 1,
            "target_user_id": self.__user_id__,
            "last_id": self.__last_video_id__,
            "section": "videos",
            "format": "application/json",
            "id": "UserVideosMod",
        }

        module_url = PreparedRequest()
        module_url.prepare_url(self.__module_url__, params)

        parsed_archive_url = urlparse(self.archive_url)

        #

        query_url = f"{parsed_archive_url.scheme}://{parsed_archive_url.netloc}/{'/'.join(parsed_archive_url.path.split('/')[1:3])}/{module_url.url}"

        r = requests.get(query_url)

        json_data = json.loads(r.text)

        if json_data["body"] == "":
            self.__last_video_fetched__ = True
            return

        soup_body = BeautifulSoup(json_data["body"], "html.parser")

        # TODO: Parse videos from json body attribute

        # foreach .video-item get href from info div
        # after retrieving this, take video_id from href (second element in path)
        # create embeds url for this video_id
        # in case recursive function case is hit, check availability of all videos
        # after which the recursive function ends
        # ONLY ADD UNIQUE ID
        self.videos += video_list

        self.__current_page_number__ += 1
        # TODO: Test recursive function
        self.get_more_videos()

    def download_videos(self, output_path: str) -> None:
        for video_index in track(range(len(self.videos)), "Downloading videos..."):
            current_video: Video = self.videos[video_index]
            if not current_video.valid:
                continue
            structured_info("download", f"Attempting to download {current_video.title}")
            current_video.download_video(output_path)

    def check_availability(self) -> bool:
        availability_api = WaybackMachineAvailabilityAPI(
            self.original_url, self.__wayback_user_agent__
        )

        possible_url = availability_api.near(
            year=self.__archive_date__.year,
            month=self.__archive_date__.month,
            day=self.__archive_date__.day,
        )

        try:
            possible_url_timestamp = possible_url.timestamp()
        except ValueError as ex:
            structured_error(
                "availability",
                f"Could not find snapshot of the profile for {self.username}",
            )
            structured_error("availability", ex)
            return False
        else:
            structured_info(
                "availability", f"Found snapshot of the profile for {self.username}"
            )

        possible_url_datetime: datetime = datetime(
            year=possible_url_timestamp.year,
            month=possible_url_timestamp.month,
            day=possible_url_timestamp.day,
        )

        if self.__archive_date__ != possible_url_datetime:
            structured_warning(
                "availability", "Available date is not ideal archive date"
            )

        self.archive_url = possible_url.archive_url
        return True

    def get_initial_videos(self) -> None:
        structured_info("")
        response = requests.get(self.archive_url)
        soup = BeautifulSoup(response.content, "html.parser")

        video_data = [
            json.loads(x.string)
            for x in soup.find_all("script", type="application/ld+json")
        ][0]["video"]

        self.videos = [
            Video(id=str(x["embedURL"]).split("/")[-1], title=x["name"], description="")
            for x in video_data
        ]

        self.__last_video_id__ = self.videos[-1].id

    def expand_video_ids(self) -> None:
        # Query with last video id

        # Set last video id with id of last video in query, if none set complete
        pass


def get_profile(user: str) -> UserProfile:
    """
    Create a userprofile for given user
    """
    structured_info("Initialization", f"Getting profile for {user}")

    newUser = UserProfile(user)

    if not newUser.check_availability():
        return None

    return newUser


def structured_print(subject: str, message: str, color: str):
    print(f"[bold {color}]{subject.title()}: [/bold {color}][{color}]{message}")


def structured_info(subject: str, message: str):
    color = "bright_blue"
    print(f"[bold {color}]Info - {subject.title()}: [/bold {color}]{message}")


def structured_error(subject: str, message: str):
    structured_print(f"error - {subject}", message, "red")


def structured_warning(subject: str, message: str):
    structured_print(f"warning - {subject}", message, "bright_yellow")
