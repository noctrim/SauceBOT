import boto3

dynamodb = boto3.resource('dynamodb')
GUILD_CONFIG = dynamodb.Table("GuildConfig")
SAUCE_PHOTOS = dynamodb.Table("SaucePhotos")
DISCORD = dynamodb.Table("Discord")


def get_config(gid, key=None):
    """
    Gets current config for a specific guild.
    """
    resp = GUILD_CONFIG.get_item(
        Key={
            'Guild': str(gid)
        })
    item = resp['Item'] if 'Item' in resp else {}
    if key:
        if key in item:
            val = item[key]
            return int(val) if val.isnumeric() else val
        else:
            return None
    else:
        return item


def clear_table():
    """
    Clears sauce table of all seen photos
    """
    scan = SAUCE_PHOTOS.scan()
    with SAUCE_PHOTOS.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key=each)


def get_current_photo_count():
    """
    Gets the current number of photos inside sauce table
    """
    return SAUCE_PHOTOS.scan()["Count"]


def get_all_seen_photos():
    """
    Gets titles of all saved photos

    :return: list of titles
    """
    return [each["Filename"] for each in SAUCE_PHOTOS.scan()["Items"]]


def add_photo_to_table(filename):
    """
    Adds a photo to table

    :param filename: name of file seen
    """
    SAUCE_PHOTOS.put_item(Item={
        "Filename": filename
    })


def is_match_database(key, val, update=True):
    """
    Checks if a given key matches a specific value in bot table.
    Will update if new val seen

    :param key: key to check
    :param val: expected val
    :param update: flag to disable updating
    :return: bool if val matches
    """
    actual = get_database(key)
    if actual == val:
        return True

    if update:
        DISCORD.put_item(Item={
            "Id": key,
            "Value": val
        })

    return False

def get_database(key):
    resp = DISCORD.get_item(
        Key={
            'Id': key
        }
    )
    if "Item" in resp:
        item = resp["Item"]
    else:
        item = None
    return item['Value'] if item else None
