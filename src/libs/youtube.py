#import youtube_dl
import os
import re
import requests

from apiclient.discovery import build

from ..libs.database import is_match_database

YOUTUBE_API_KEY = os.environ['YOUTUBE_TOKEN']
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


def check_youtube(channel_id, db_key):
    """
    Checks if a given youtube channel has a new video posted that we haven't seen in DB

    :param channel_id: channel naem
    :param db_key: db location of last seen video
    """
    html = requests.get("https://www.youtube.com/c/{}/videos".format(channel_id)).text
    info = html.split("videoId", 2)
    snippet = info[1]
    r = r'\"text\":\"(.*?)\".*?\"url\":\"(.*?)\"'
    m = re.search(r, snippet)
    title = m.group(1)
    link = m.group(2)
    if is_match_database(db_key, title):
        return None
    return "https://www.youtube.com{}".format(link)
