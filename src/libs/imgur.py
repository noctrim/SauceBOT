import os

from imgurpython import ImgurClient

IMGUR_CLIENT_ID = os.environ['IMGUR_CLIENT_ID']
IMGUR_SECRET = os.environ['IMGUR_SECRET']
IMGUR_ACCESS_TOKEN = os.environ['IMGUR_ACCESS_TOKEN']
IMGUR_REFRESH_TOKEN = os.environ['IMGUR_REFRESH_TOKEN']
IMGUR_ALBUM_ID = "77SfNRz"
imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET)
imgur.set_user_auth(IMGUR_ACCESS_TOKEN, IMGUR_REFRESH_TOKEN)


def overwrite_last_image(filename):
    """
    Overwrites the last image in album

    :param filename: filename to upload in replacement
    """
    uploaded_img = imgur.upload_from_path(filename, anon=False)
    album = imgur.get_album(IMGUR_ALBUM_ID)
    imgur.delete_image(album.images[0]['id'])
    imgur.album_add_images(IMGUR_ALBUM_ID, [uploaded_img['id']])
    return uploaded_img
