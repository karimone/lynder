import logging
import datetime

from .cookie import Cookie

from bs4 import BeautifulSoup
import requests


_logger = logging.getLogger(__name__)


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
        self.chapters = kwargs.get("chapters", None)

    def get_markdown(self) -> str:

        # TODO: software tags can be empty

        result = f"""
        **Title:** {self.title}
        **Author:** {self.author}
        **Release date:** {self.release_date}
        **Download date:** {self.download_date}
        **Time Required:** {self.time_required}
        **Difficult Level:** {self.difficult_level}
        **Subject Tags:** {self.subject_tags}
        **Software Tags:** {self.software_tags}

        "**Description:**
        
        {self.description}
        """
        return result

    def get_text(self):
        pass


class LyndaTutorial:

    def __init__(self, link: str, user: str=None , password: str=None, cookie: Cookie=None):
        self._user = user
        self._password = password
        self._cookie = Cookie
        self._link = link
        self._client = requests

        # if (self._user and self._password) or self._cookie:
        #     pass

    def get_tutorial_data(self) -> LyndaTutorialData:
        data = self._get_tutorial_data()
        return LyndaTutorialData(**data)

    def _get_tutorial_data(self) -> dict:
        tutorial = {}
        response = self._client.get(self._link)
        _logger.debug("Get response %s for link %s", response, self._link)

        soup = BeautifulSoup(response.text, "html.parser")
        tutorial["title"] = soup.find('h1', attrs={'class': 'default-title'}).text.strip()
        tutorial["author"] = soup.find('cite', attrs={'data-ga-label': 'author-name'}).text.strip()
        tutorial["release_date"] = soup.find('span', attrs={'id': 'release-date'}).text.strip()
        tutorial["time_required"] = soup.find('span', attrs={'itemprop': 'timeRequired'}).text.strip()
        tutorial["description"] = soup.find('div', attrs={'itemprop': 'description'}).text.strip()
        tutorial["difficult_level"] = soup.find('div', attrs={'class': 'course-info-stat-cont'}).find(
                'strong').text.strip()

        # tutorial["exercise_file"] = soup.find('section', attrs={'id':'tab-exercise-files'}).text or ""

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

