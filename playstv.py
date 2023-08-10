from datetime import datetime
import json
from pprint import pprint
from typing import Self
from bs4 import BeautifulSoup
import requests

from waybackpy import WaybackMachineAvailabilityAPI, WaybackMachineCDXServerAPI


class Video:
    def __init__(self, id: str, title: str, description: str) -> None:
        self.id: str = id
        self.valid: bool = False
        self.title: str = title
        self.description: str = description
        self.original_url: str = f"https://plays.tv/embeds/{self.id}"
        self.archive_url: str = str()
        self.__archive_date__: datetime = datetime(year=2019, month=12, day=10, hour=17)
        self.__wayback_user_agent__: str = str(
            "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        )

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

        if possible_url is None:
            return False

        self.valid = True
        self.archive_url = possible_url.archive_url

        return True

    # TODO ADD FUNCTION FOR CHECKING VID AVAILABILITY


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

        if possible_url is None:
            return False

        possible_url_timestamp = possible_url.timestamp()

        possible_url_datetime: datetime = datetime(
            year=possible_url_timestamp.year,
            month=possible_url_timestamp.month,
            day=possible_url_timestamp.day,
            hour=possible_url_timestamp.hour,
        )

        if self.__archive_date__ != possible_url_datetime:
            print("WARNING: available date is not ideal archive date")

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
        ]

        self.__last_video_id__ = self.videos[-1].id

    def get_videos(self) -> None:
        for id in self.video_ids:
            self.videos

    def expand_video_ids(self) -> None:
        # Query with last video id

        # Set last video id with id of last video in query, if none set complete
        pass


def get_profile(user: str) -> UserProfile:
    """
    Create a userprofile for given user
    """

    newUser = UserProfile(user)

    if not newUser.check_availability():
        return None

    return newUser


if __name__ == "__main__":
    me = get_profile("QUonan")
    me.get_initial_video_ids()

    for vid in me.videos:
        vid.check_availability()

    print(me)
