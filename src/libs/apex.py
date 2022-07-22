import os
import requests
import shutil

from PIL import Image

from ..libs.database import is_match_database

APEX_TOKEN = os.environ['APEX_TOKEN']


def get_crafting_items():
    """
    Grabs the current list of crafting items from API
    and saves them locally

    :return: list of item paths
    """
    r = requests.get("https://api.mozambiquehe.re/crafting?auth={}".format(APEX_TOKEN))
    files = []
    for item in r.json():
        if "start" in item:
            content = item['bundleContent']
            for i in content:
                asset = i['itemType']['asset']
                basename = os.path.basename(asset)
                r = requests.get(asset, stream=True)
                if r.status_code == 200:
                    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                    r.raw.decode_content = True
                    # Open a local file with wb ( write binary ) permission.
                    with open(basename, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    files.append(basename)
    return files


def generate_crafting_image(filename="rotation.png", force=False):
    """
    Generates a crafting image of current rotation
    If is same as last seen rotation will skip

    :param filename: output filename
    :param force: to force creation even if same
    """
    def cleanup(files):
        for f in files:
            os.remove(f)

    files = get_crafting_items()
    if not force and is_match_database('apex_rotation', "".join(files)):
        cleanup(files)
        return
    template_main = Image.open("res/template.png")
    template = template_main.copy()
    starting_point = (5, 35)
    for i, f in enumerate(files):
        img = Image.open(f)
        img = img.resize((102, 102))
        if i == 2:
            point = starting_point
        elif i == 0:
            point = (starting_point[0], starting_point[1] + 143)
        elif i == 3:
            point = (starting_point[0] + 107, starting_point[1])
        elif i == 1:
            point = (starting_point[0] + 107, starting_point[1] + 143)
        template.paste(img, (point))
    filename = "rotation.png"
    template.save(filename)
    cleanup(files)
    return filename
