import os
import re
import unicodedata


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


def get_or_create_folder(path: str, folder_name: str) -> str:
    folder_name_slugified = slugify(folder_name)
    complete_path = os.path.join(path, folder_name_slugified)
    if not os.path.exists(complete_path):
        os.mkdir(complete_path)
    return folder_name_slugified
