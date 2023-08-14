from datetime import datetime
import json
from operator import concat
import os
from time import sleep
from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
from requests.models import PreparedRequest
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
            file_name = concat(self.title, ".mp4")
            file_path = os.path.join(output_path, file_name)

            if os.path.isfile(file_path):
                return

            video_stream = requests.get(self.video_url, stream=True)

            with open(file_path, "wb") as file:
                for chunk in video_stream.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        except:
            structured_error("download", f"Failed to download {self.title}")
            sleep(2)
            return

    def check_availability(self) -> bool:
        if self.valid:
            return True
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
        self.__more_video_error__: bool = False
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
        structured_info(
            "Availability",
            f"Checking availability of videos (total: {len(self.videos)})",
        )
        for vid_index in track(
            range(len(self.videos)), description="Checking video availability..."
        ):
            current_vid: Video = self.videos[vid_index]
            current_vid.check_availability()

        valid_videos = [x for x in self.videos if x.valid]
        structured_info(
            "Availability",
            f"[green]Successfully checked availability of videos ({len(valid_videos)} out of {len(self.videos)} valid)",
        )

    def get_more_videos(self, timestamp: str | None = None) -> list[Video] | None:
        if self.__current_page_number__ == 0:
            structured_info("more videos", "Starting queries for more videos")
            self.__current_page_number__ += 1
        if self.__last_video_fetched__:
            structured_info(
                "more videos", "[green]Succesfully querried for more videos"
            )
            return

        if self.__more_video_error__:
            structured_warning("more videos", "Stopping queries for more videos")
            return

        video_list: list[Video] = []

        params = {
            "section": "videos",
            "page_num": self.__current_page_number__,
            "target_user_id": self.__user_id__,
            "infinite_scroll": True,
            "last_id": self.__last_video_id__,
            "custom_loading_module_state": "appending",
            "infinite_scroll_fire_only": True,
            "format": "application/json",
            "id": "UserVideosMod",
        }

        module_url = PreparedRequest()
        module_url.prepare_url(self.__module_url__, params)

        parsed_archive_url = urlparse(self.archive_url)

        #
        if not timestamp:
            query_url = f"{parsed_archive_url.scheme}://{parsed_archive_url.netloc}/{'/'.join(parsed_archive_url.path.split('/')[1:3])}/{module_url.url}"
        else:
            query_url = f"{parsed_archive_url.scheme}://{parsed_archive_url.netloc}/{parsed_archive_url.path.split('/')[1]}/{timestamp}/{module_url.url}"

        try:
            r = requests.get(query_url)
        except:
            structured_error(
                "more videos", "failed to retrieve more videos from playstv api"
            )

        try:
            json_data = json.loads(r.text)
        except:
            alternate_timestamp = "20191210164752"
            if parsed_archive_url.path.split("/")[2] != alternate_timestamp:
                structured_warning(
                    "more videos",
                    "Failed to parse JSON, retrying with different timestamp",
                )
                self.get_more_videos(alternate_timestamp)
            else:
                structured_error("more videos", "JSON parsing error")
                self.__more_video_error__ = True
                return

        if json_data["body"] == "":
            self.__last_video_fetched__ = True
        else:
            soup_body = BeautifulSoup(json_data["body"], "html.parser")
            # Get video-items
            video_item_elements = soup_body.find_all("li", {"class": "video-item"})
            current_ids = [x.id for x in self.videos]

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
                    structured_warning(
                        "more videos", f"Could not get title for {video_id}"
                    )
                    continue

                video_list.append(Video(video_id, title, ""))
                current_ids.append(video_id)

            self.videos += video_list
            self.__last_video_id__ = current_ids[-1]
            self.__current_page_number__ += 1
            structured_info(
                "More videos",
                f"[bright_green]Successfully added [bold]{len(video_list)} videos[/bold] (total: {len(self.videos)})",
            )
        # TODO: Test recursive function
        self.get_more_videos()

    def download_videos(self, output_path: str) -> None:
        valid_videos: list[Video] = [x for x in self.videos if x.valid]
        structured_info(
            "download", f"Starting download process for {len(valid_videos)} videos"
        )
        for video_index in track(range(len(valid_videos)), "Downloading videos..."):
            current_video: Video = self.videos[video_index]
            current_video.download_video(output_path)
        structured_info("download", "[green]Successfully completed download process")

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
        structured_info("initial videos", "Getting initial videos from profile page")
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
        structured_info(
            "initial videos", "[green]Successfully retrieved initial videos"
        )

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
