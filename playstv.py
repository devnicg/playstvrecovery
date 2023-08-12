from datetime import datetime
import json
from operator import concat
import os
from pathlib import Path
from time import sleep
from typing import Annotated, Optional
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
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
        self.__last_video_fetched__: bool = False
        self.__last_video_id__: str = str()
        self.__archive_video_data__: [] = []
        self.__wayback_user_agent__: str = str(
            "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        )
        self.__archive_date__: datetime = datetime(year=2019, month=12, day=10, hour=17)

    def __str__(self) -> str:
        return f"---------\nUsername: {self.username} \nPossible videos: {len(self.video_ids)} \nActual Videos {len(self.videos)} \n---------"

    def get_id_from_url(url: str) -> str:
        pass

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
            hour=self.__archive_date__.hour,
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
            hour=possible_url_timestamp.hour,
        )

        if self.__archive_date__ != possible_url_datetime:
            structured_warning(
                "availability", "Available date is not ideal archive date"
            )

        self.archive_url = possible_url.archive_url
        return True

    def get_initial_video_ids(self) -> None:
        response = requests.get(self.archive_url)
        soup = BeautifulSoup(response.content, "html.parser")

        video_data = [
            json.loads(x.string)
            for x in soup.find_all("script", type="application/ld+json")
        ][0]["video"]

        self.videos = [
            Video(id=str(x["embedURL"]).split("/")[-1], title=x["name"], description="")
            for x in video_data
        ][:5]
        # TODO: Remove first 5 element selector

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


app = typer.Typer()


@app.command()
def main(output_path: Annotated[Optional[Path], typer.Option()]):
    if not output_path.is_dir():
        structured_error("initialization", "Specified path is not a directory")
        return

    user = typer.prompt("What's your Plays.tv username?")
    me = get_profile(user)

    if me is None:
        structured_error("initialization", "Could not get user profile")
        return

    me.get_initial_video_ids()

    for vid_index in track(
        range(len(me.videos)), description="Checking video availability..."
    ):
        current_vid: Video = me.videos[vid_index]
        current_vid.check_availability()

    me.download_videos(output_path.name)


if __name__ == "__main__":
    app()
