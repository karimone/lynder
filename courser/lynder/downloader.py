
import logging
import os

from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Optional
from urllib.parse import urlsplit

from lynder.cookie import Cookie
from lynder.lecture import Lecture
from lynder.settings import settings
from lynder.lynda import Lynda
from lynder.pluralsight import Pluralsight

_logger = logging.getLogger(__name__)

DispatcherRule = namedtuple("DispatcherRule", ["domain", "service"])
dispatcher_map = (
    DispatcherRule(domain="lynda.com", service=Lynda),
    DispatcherRule(domain="pluralsight.com", service=Pluralsight),
)


def _get_service_name(netloc: str) -> Optional[str]:
    for rule in dispatcher_map:
        print(f"Checking {rule.domain} in {netloc}")
        if rule.domain in netloc:
            return rule.service
    return None


def dispatcher(url: str):
    url_split = urlsplit(url)
    netloc = url_split.netloc if url_split.scheme else url_split.path
    assert netloc
    Service = _get_service_name(netloc)
    if Service:
        print(f"Service {Service} found for the url {url}")
        service = Service(url)

    else:
        print(f"No service found for the url {url}")


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

