
import logging
import os

from abc import ABC, abstractmethod

from lynder.cookie import Cookie
from lynder.lecture import Lecture
from lynder.settings import settings

_logger = logging.getLogger(__name__)


def dispatcher(link: str):
    print(f"dispatched for the link {link}")


class BaseDownloader(ABC):

    def __init__(self, link: str,
                 user: str = None,
                 password: str = None,
                 cookie: Cookie = None):
        pass

    @abstractmethod
    def download(self, lecture: Lecture):
        pass


class YoutubeDL:
    pass


class YoutubeDownloader(BaseDownloader):

    def download(self, lecture: Lecture):
        if settings.COOKIES:
            authentication = f"--cookies {settings.COOKIES}"
        else:
            authentication = f"--username {settings.USERNAME} --password {settings.PASSWORD}"

        if settings.VERBOSE:
            print(f"Downloading ({lecture.index}) {lecture.title}")

        filename = f"{lecture.index+1} - %(title)s.%(ext)s"

        os.system(f"youtube-dl --output \"{filename}\" --write-sub --embed-subs {authentication} {lecture.title} | grep download")

        if settings.VERBOSE:
            print(f"Downloaded.")

