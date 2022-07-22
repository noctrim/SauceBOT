import os
import psycopg2

from contextlib import contextmanager
from urllib.parse import urlparse

DATABASE_URL = os.environ["DATABASE_URL"]
raw_info = urlparse(DATABASE_URL)
DATABASE_INFO = {
    "host": raw_info.hostname, "user": raw_info.username,
    "password": raw_info.password, "database": raw_info.path[1:],
    "port": raw_info.port}


@contextmanager
def connect():
    """
    Helper function to make sure DB is closed
    """
    conn = psycopg2.connect(**DATABASE_INFO)
    conn.autocommit = True
    cur = conn.cursor()
    yield cur
    conn.close()


def clear_table():
    """
    Clears sauce table of all seen photos
    """
    with connect() as cur:
        cur.execute("truncate sauce_photos")


def get_current_photo_count():
    """
    Gets the current number of photos inside sauce table
    """
    with connect() as cur:
        cur.execute("select count(*) from sauce_photos")
        return cur.fetchone()[0]


def get_all_seen_photos():
    """
    Gets titles of all saved photos

    :return: list of titles
    """
    with connect() as cur:
        cur.execute("select * from sauce_photos")
        return [p[1] for p in cur.fetchall()]


def add_photo_to_table(filename):
    """
    Adds a photo to table

    :param filename: name of file seen
    """
    id_ = get_current_photo_count() + 1
    with connect() as cur:
        cur.execute("insert into sauce_photos(id, name) values(%s, %s)", (id_, filename))


def is_match_database(key, val, update=True):
    """
    Checks if a given key matches a specific value in bot table.
    Will update if new val seen

    :param key: key to check
    :param val: expected val
    :param update: flag to disable updating
    :return: bool if val is new
    """
    with connect() as cur:
        cur.execute("select * from discord where key = %s", (key,))
        res = cur.fetchone()
        if res:
            i, dbkey, dbval = res
            if dbval == val:
                return True
            if update:
                cur.execute("update discord set value = %s where id = %s", (val, i))
        else:
            print("Couldn't Find [{}] in DB".format(key))
        return False
