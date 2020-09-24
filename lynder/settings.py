import os


class Settings:
    """Simple singleton to have a setting available in the project"""

    instance = None

    class __Settings:
        HOME_DIR = os.getcwd()
        WORKER_NUM = 2
        COOKIES = None

    def __init__(self):
        Settings.instance = Settings.instance if Settings.instance else Settings.__Settings()

    def __setattr__(self, key, value):
        return setattr(self.instance, key, value)

    def __getattr__(self, name):
        return getattr(self.instance, name)


settings = Settings()
