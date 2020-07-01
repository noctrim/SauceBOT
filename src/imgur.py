import os
import pyimgur
import requests

IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
IMGUR_ALBUM_ID = "XNDQTsC"


class ImgurBehavior:
    def __init__(self):
        self.client = pyimgur.Imgur(IMGUR_CLIENT_ID)

    def download_file(self, url, name='tmp.jpg'):
        print(url)
        resp = requests.get(url)
        if resp.status_code == 200:
            print("Response Recieved. Downloading File: {0}".format(url))
            with open(name, 'wb') as f:
                f.write(resp.content)
                f.close()
                return name
        else:
            print("Error Code: {0} Downloading File: {1}".format(
                resp.status_code, url))

    def get_album(self):
        return self.client.get_album(IMGUR_ALBUM_ID)
