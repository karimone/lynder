import datetime
import logging
import os
from collections import namedtuple
from typing import List, Optional
import threading
import time
from threading import Thread

import requests
from bs4 import BeautifulSoup

from .settings import settings
from .tools import get_or_create_folder, slugify

_logger = logging.getLogger(__name__)


LyndaLecture = namedtuple("LyndaLecture", ["index", "title", "url"])


class LyndaChapter:

    def __init__(self, title: str, lectures: List[LyndaLecture],
                 index: int = None):
        self.index = index
        self.title = title
        self.lectures = lectures


class LyndaTextFormat:
    MARKDOWN = "md"
    TEXT = "txt"


class LyndaContextFile:
    OVERVIEW = "overview"
    CONTENT = "content"


class LyndaTutorialData:

    def __init__(self, **kwargs):
        self.title = kwargs.get("title", None)
        self.author = kwargs.get("author", None)
        self.difficult_level = kwargs.get("difficult_level", None)
        self.release_date = kwargs.get("release_date", None)
        self.time_required = kwargs.get("time_required", None)
        self.description = kwargs.get("description", None)
        self.subject_tags = kwargs.get("subject_tags", None)
        self.software_tags = kwargs.get("software_tags", None)
        self.download_date = kwargs.get("download_date", None)
        self.chapters = self._enrich_chapters(kwargs.get("chapters", None))

    def _enrich_chapters(self, chapters) -> List[LyndaChapter]:
        chapters_objects = []
        for chapter_title, lectures in chapters.items():
            lectures_objects = []
            for index, lecture in enumerate(lectures):
                lectures_objects.append(LyndaLecture(index=index, title=lecture[0], url=lecture[1]))

            chapters_objects.append(LyndaChapter(title=chapter_title, lectures=lectures_objects))

        return chapters_objects

    def _get_overview_md(self) -> str:
        # TODO: software tags can be empty

        result = f"""**Title:** {self.title}
**Author:** {self.author}
**Release date:** {self.release_date}
**Download date:** {self.download_date}
**Time Required:** {self.time_required}
**Difficult Level:** {self.difficult_level}
**Subject Tags:** {", ".join(self.subject_tags)}
**Software Tags:** {", ".join(self.software_tags) if self.software_tags else " -"}

**Description:**

{self.description}
"""
        return result

    def _get_content_md(self) -> str:
        result = f"# {self.title} by {self.author} on lynda.com\n\n"
        for chapter in self.chapters:
            result += f"## {chapter.title}\n\n"
            for lecture in chapter.lectures:
                result += f"\t- {lecture.title}\n"
            result += "\n"

        return result

    def get_overview(self, format: str) -> str:
        return self._get_generic(context_file=LyndaContextFile.OVERVIEW, format=format)

    def get_content(self, format: str) -> str:
        return self._get_generic(context_file=LyndaContextFile.CONTENT, format=format)

    def _get_generic(self, context_file: str, format: str) -> str:
        func = getattr(self, f"_get_{context_file}_{format}")
        if func:
            return func()
        raise NotImplemented(f'The {context_file} for {format} is not implemented')


class LyndaTutorial:

    def __init__(self, page_data: str):
        self._page_data = page_data

    def get_tutorial_data(self) -> LyndaTutorialData:
        data = self._get_tutorial_data()
        return LyndaTutorialData(**data)

    def _get_tutorial_data(self) -> dict:
        tutorial = {}
        soup = BeautifulSoup(self._page_data, "html.parser")
        tutorial["title"] = soup.find('h1', attrs={'class': 'default-title'}).text.strip()
        tutorial["author"] = soup.find('cite', attrs={'data-ga-label': 'author-name'}).text.strip()
        tutorial["release_date"] = soup.find('span', attrs={'id': 'release-date'}).text.strip()
        tutorial["time_required"] = soup.find('span',
                                              attrs={'itemprop': 'timeRequired'}).text.strip()
        tutorial["description"] = soup.find('div', attrs={'itemprop': 'description'}).text.strip()
        tutorial["difficult_level"] = soup.find('div',
                                                attrs={'class': 'course-info-stat-cont'}).find(
                'strong').text.strip()

        # tutorial["exercise_file"] = soup.find('section', attrs={
        # 'id':'tab-exercise-files'}).text or ""

        tutorial["subject_tags"] = [tag.text.strip() for tag in
                                    soup.findAll('a', attrs={'data-ga-label': 'topic-tag'})]
        tutorial["software_tags"] = [tag.text.strip() for tag in
                                     soup.findAll('a', attrs={'data-ga-label': 'software-tag'})]
        tutorial["download_date"] = datetime.datetime.now().strftime("%b %d, %Y")

        chapters = {}
        toc = soup.find('ul', attrs={'class': 'course-toc'})
        for index, chapter in enumerate(toc.find_all('li', attrs={'role': 'presentation'})):
            ch = chapter.find('h4', attrs={'data-ga-label': 'toc-chapter'})
            if ch:
                lectures = []
                for lecture in chapter.find_all('a', attrs={'class': 'video-name'}):
                    lectures.append((lecture.text.strip(), lecture["href"]))
                chapters[ch.text.strip().replace(":", " -").replace('/', "-")] = lectures

        tutorial["chapters"] = chapters
        return tutorial



class LyndaAuthorCourse:
    def __init__(self, author: str, title: str, duration: str, release: str, url: str, description: str):
        self.author = author
        self.title = title
        self.duration = duration
        self.release = release
        self.url = url
        self.description = description


class LyndaAuthorData:
    def __init__(self, author: str, courses: List[LyndaAuthorCourse]):
        self.author = author
        self.courses = courses


class LyndaAuthor:
    def __init__(self, page_data: str):
        self._page_data = page_data
        self._soup = BeautifulSoup(self._page_data, "html.parser")
        self._author = None

    def _get_author(self) -> Optional[str]:
        if self._author:
            return self._author
        breadcrumbs = self._soup.find('div', attrs={'class': 'breadcrumbs'})
        if not breadcrumbs:
            return None
        all_author = breadcrumbs.findChild('a').text.strip()
        if all_author.lower() != "All Authors".lower():
            return None
        author = breadcrumbs.findChild('span').text.strip()
        self._author = author
        return author

    def _get_courses(self) -> List[LyndaAuthorCourse]:
        author = self._get_author()
        result = []
        courses = self._soup.find_all("li", attrs={"data-result-type": "COURSE"})
        for course in courses:
            a = course.findChild("a")
            url = a.attrs['href']
            title = course.find("h3").text.strip()
            duration = course.find("span", attrs={"class": "meta-duration"}).text.strip()
            release = course.find("span", attrs={"class": "release-date"}).text.strip()
            description = course.find("div", attrs={"class": "meta-description"}).text.strip()
            result.append(LyndaAuthorCourse(author=author,
                                            url=url,
                                            title=title,
                                            duration=duration,
                                            release=release,
                                            description=description))
        return result

    def get_author_data(self) -> LyndaAuthorData:
        return LyndaAuthorData(author=self._get_author(), courses=self._get_courses())


class Lynda:

    AUTHOR_PAGE = 'author'
    TUTORIAL_PAGE = 'tutorial'

    def __init__(self, url: str):
        self._url = url
        self._page_data = None
        self._soup = None
        self._create_soup()
        self.parse_url()

    def _create_soup(self):
        response = requests.get(self._url)
        _logger.debug("Get response %s for link %s", response, self._url)
        self._page_data = response.text
        self._soup = BeautifulSoup(self._page_data, "html.parser")

    def _determine_type_of_page(self) -> Optional[str]:
        """Returns the author name or nothing"""
        breadcrumbs = self._soup.find('div', attrs={'class': 'breadcrumbs'})
        if not breadcrumbs:
            return Lynda.TUTORIAL_PAGE
        all_author = breadcrumbs.findChild('a').text.strip()
        if all_author.lower() != "All Authors".lower():
            return None
        author = breadcrumbs.findChild('span').text.strip()
        return Lynda.AUTHOR_PAGE

    def parse_url(self):
        type_of_page = self._determine_type_of_page()
        if type_of_page == Lynda.AUTHOR_PAGE:
            self.run_author_download()
        elif type_of_page == Lynda.TUTORIAL_PAGE:
            self.run_tutorial_download(self._url)

    def run_author_download(self):

        lynda_author = LyndaAuthor(page_data=self._page_data)
        lynda_author_data = lynda_author.get_author_data()

        author_slugified = get_or_create_folder(path=os.getcwd(), folder_name=lynda_author_data.author)
        os.chdir(author_slugified)
        total_courses = len(lynda_author_data.courses)

        info_text = f"# Author {lynda_author_data.author}\n\n"
        info_text += f"Full download of author courses\n"

        for n, course in enumerate(lynda_author_data.courses, start=1):
            print(f"[{n}/{total_courses}] > {course.title}")
            self.run_tutorial_download(course.url)
            info_text += f"\n## {course.title}\n\n"
            info_text += f"\t - **Duration:** {course.duration}\n"
            info_text += f"\t - **Release:** {course.release}\n"
            info_text += f"\t - **Description:** {course.description}\n"
            info_text += f"\t - **Url:** {course.url}\n\n"

        info_file = open("INFO.md", "w")
        info_file.write(info_text)
        info_file.close()

    def _save_tutorial_info_files(self, tutorial_data: LyndaTutorialData):
        content_data = tutorial_data.get_content(format=LyndaTextFormat.MARKDOWN)
        content = open("CONTENT.md", "w")
        content.write(content_data)
        content.close()

        overview_data = tutorial_data.get_overview(format=LyndaTextFormat.MARKDOWN)
        overview = open("OVERVIEW.md", "w")
        overview.write(overview_data)
        overview.close()

    def _download_chapters(self, tutorial_data: LyndaTutorialData):
        for chapter in tutorial_data.chapters:
            chapter_slugified = get_or_create_folder(path=os.getcwd(), folder_name=chapter.title)
            os.chdir(chapter_slugified)

            for lecture in chapter.lectures:
                while threading.activeCount() > settings.WORKER_NUM:
                    time.sleep(5)
                th = Thread(target=download_lecture, kwargs={"lecture": lecture})
                th.deamon = True
                th.start()
                th.join()

            os.chdir("..")

    def run_tutorial_download(self, url: str):
        response = requests.get(url)
        lynda_tutorial = LyndaTutorial(response.text)
        tutorial_data = lynda_tutorial.get_tutorial_data()
        print(f"Running download for tutorial: {tutorial_data.title}")
        folder = get_or_create_folder(path=os.getcwd(), folder_name=tutorial_data.title)
        os.chdir(folder)

        self._save_tutorial_info_files(tutorial_data)
        self._download_chapters(tutorial_data)
        os.chdir("..")

        # print("DOWNLOADING IS DONE")
        # if settings.silent is None:
        #     os.system("open .")


def download_lecture(lecture: LyndaLecture):
    if settings.COOKIES:
        authentication = "--cookies " + settings.COOKIES
    else:
        authentication = "--username " + settings.USERNAME + " --password " + settings.PASSWORD

    # print(f"Downloading: {lecture.title}...")
    youtube_dl_filename = f"{str(lecture.index)} - %(title)s.%(ext)s"
    os.system(f"youtube-dl --output \"{youtube_dl_filename}\" --write-sub "
              f"--embed-subs {authentication} {lecture.url} | grep download")
    # print("...done.")
    print()


