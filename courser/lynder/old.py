#!/usr/local/bin/python3

import argparse
import datetime
import logging
import os
import threading
import time
from threading import Thread
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

from .settings import settings

_logger = logging.getLogger(__name__)

LinkType = namedtuple("LinkType", ["tutorial", "author", "path"])



def _analyse_link(link: str) -> LinkType:

    # get the link selector with the url
    # author-page > div.title-banner > div > link
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "html.parser")

def download(link: str):
    pass

def download_tutorial(link):
    os.chdir(settings.HOME_DIR)
    tutorial = get_tutorial_data(link)
    create_folders(tutorial)
    create_overview_md(tutorial)
    create_content_md(tutorial)
    download_videos(tutorial)
    return tutorial

def create_folders(tutorial):
    for char in ' ?.!/;:öä':
        tutorial["title"] = tutorial["title"].replace(char, '')
    if not os.path.exists(tutorial["title"]):
        os.mkdir(tutorial["title"])
        print("\t\"" + tutorial["title"] + "\" folder is created.")
    else:
        print("\t\"" + tutorial["title"] + "\" folder already exists.")
    os.chdir(tutorial["title"])
    for chapter in tutorial["chapters"]:
        if not os.path.exists(chapter):
            os.mkdir(chapter)
            print("\t\"" + chapter + "\" folder is created.")



def create_content_md(tutorial):
    content = open("CONTENT.md", "w")
    content.write("# " + tutorial["title"] + " with " + tutorial["author"] + " on lynda.com \n")
    for chapter, lectures in tutorial["chapters"].items():
        content.write("## " + chapter + "\n")
        for lecture in lectures:
            content.write("### " + lecture[0] + "\n")
        content.write("\n")
    content.close()
    print("\tCONTENT.md is created.")


def download_videos(tutorial):
    for chapter, lectures in tutorial["chapters"].items():
        os.chdir(chapter)
        for index, lecture in enumerate(lectures):
            while (threading.activeCount() > settings.WORKER_NUM):
                time.sleep(5)
            th = Thread(target=download_lecture, args=(lecture, index,))
            th.deamon = True
            th.start()
            th.join()

        os.chdir("..")
    print("DOWNLOADING IS DONE")
    if settings.silent is None:
        os.system("open .")


def download_lecture(lecture, index):
    if settings.COOKIES:
        authentication = "--cookies " + settings.COOKIES
    else:
        authentication = "--username " + settings.USERNAME + " --password " + settings.PASSWORD

    print("\n\t\"" + lecture[0] + "\" is downloading...")
    os.system("youtube-dl --output \"" + str( index + 1) + " - %(title)s.%(ext)s\" --write-sub --embed-subs " + authentication + " " + lecture[1] + " | grep download")
    print("\t\"" + lecture[0] + "\" was downloaded.")


