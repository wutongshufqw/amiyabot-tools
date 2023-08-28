from core import GitAutomation

from .config import data_path


def download_data():
    url = 'https://gitlab.com/wutongshufqw/immortal.git'
    GitAutomation(data_path, url).update()
