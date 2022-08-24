import discord
import os
import re
import requests
import youtube_dl

from apiclient.discovery import build

from ..libs.database import is_match_database

FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}
YDL_OPTIONS = {"format": "bestaudio"}

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


def get_song_iterator(title):
    """
    Gets an iterator of songs for a song title for pagination purposes

    :param title: title of song
    :return: iterator of song items
    """
    token = None
    while True:
        request = youtube.search().list(q=title + " lyrics", part='snippet', type='video', pageToken=token)
        resp = request.execute()
        token = resp.get('nextPageToken', None)
        items = resp['items']
        yield items
        if not token:
            break


async def get_stream(link):
    """
    Gets a stream object for given url link

    :return: stream
    """
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(link, download=False)
        url = info['formats'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        return source
