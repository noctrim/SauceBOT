import os
import pyimgur
import requests


IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
CLIENT = pyimgur.Imgur(IMGUR_CLIENT_ID)


class ImgurBehavior:
    """
    Wrapper class to interact with Imgur
    """
    @staticmethod
    def download_file(url, path='tmp.jpg'):
        """
        Downloads a file from imgur url

        :param url: url to download image from
        :param path: path to save image as

        :return: path if created, else None
        """
        # Try to download file
        resp = requests.get(url)
        if resp.status_code == 200:
            # Save resp into file
            print("Response Recieved. Downloading File: {0}".format(url))
            with open(path, 'wb') as f:
                f.write(resp.content)
            return path
        else:
            print("Error Code: {0} Downloading File: {1}".format(
                resp.status_code, url))

    @staticmethod
    def get_album(album_id):
        """
        Gets an albums contents from Imgur
        """
        return CLIENT.get_album(album_id)
