import asyncio
import boto3
import discord
import os
import psycopg2
import pytz
import random
import re
import requests
import shutil

from datetime import datetime
from discord.ext import commands, tasks
from imgurpython import ImgurClient
from PIL import Image
from urllib.parse import urlparse

from src.timer import Timer

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

PET_PICS_CHANNEL = 967919501037437018
STREAMER_CHANNEL = 967914669576712222
WELCOME_CHANNEL = 963877676551118909
READ_ME_CHANNEL = 963877448221593680

ROLE_REACT_MESSAGE_ID = 967193372588638218

COMMAND_OPT = "!"

DATABASE_URL = os.environ["DATABASE_URL"]
raw_info = urlparse(DATABASE_URL)
DATABASE_INFO = {
    "host": raw_info.hostname, "user": raw_info.username,
    "password": raw_info.password, "database": raw_info.path[1:],
    "port": raw_info.port}

ACTIVE_STREAMERS = {}
BASE_ROLE_NAME = "Squad"
LIVE_STREAMERS = "Live"
LIVE_STREAMERS_ROLE_MINIMUM = "ANBU Black Ops"
STREAMING_CHANNEL_NOTIFICATION_DELAY = 60

AWS_KEY = os.environ["AWS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]

session = boto3.Session(aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
s3 = session.resource('s3')
s3_bucket = s3.Bucket("noctrimphotos")
SENT_PHOTOS = set()

APEX_TOKEN = os.environ['APEX_TOKEN']
APEX_CHANNEL = 967946397846474762

OW_CHANNEL = 967946457338507304

IMGUR_CLIENT_ID = os.environ['IMGUR_CLIENT_ID']
IMGUR_SECRET = os.environ['IMGUR_SECRET']
IMGUR_ACCESS_TOKEN = os.environ['IMGUR_ACCESS_TOKEN']
IMGUR_REFRESH_TOKEN = os.environ['IMGUR_REFRESH_TOKEN']
IMGUR_ALBUM_ID = "77SfNRz"
imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET)
imgur.set_user_auth(IMGUR_ACCESS_TOKEN, IMGUR_REFRESH_TOKEN)

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(intents=intents, command_prefix=COMMAND_OPT)


# Starting OnReady
@bot.event
async def on_ready():
    """
    On ready event
    Called whenever BOT starts
    """
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    # Change default presence state
    game = discord.Game("Fetch!")

    await bot.change_presence(status=discord.Status.idle, activity=game)
    send_daily_messages.start()
    send_daily_apex_update.start()
    send_daily_ow_update.start()


# Send Daily Dog Photo To Channel
@tasks.loop(hours=24)
async def send_daily_messages():
    await send_daily_photo()


async def send_daily_photo():
    conn = psycopg2.connect(**DATABASE_INFO)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("select count(*) from sauce_photos")
    count = cur.fetchone()[0]

    avail_photos = [f for f in s3_bucket.objects.all() if not f.key.endswith("/") and "Sauce" in f.key]
    random.shuffle(avail_photos)
    for photo in avail_photos:
        if photo not in SENT_PHOTOS:
            cur.execute("insert into sauce_photos(id, name) values(%s, %s)", (count+1, photo.key))
            break
    else:
        # All photos were seen, clear and start over
        cur.execute("truncate sauce_photos")
        cur.execute("insert into sauce_photos(id, name) values(%s, %s)", (1, photo.key))
    conn.close()

    local_fp = "temp.png"
    s3_bucket.download_file(photo.key, local_fp)

    channel = bot.get_channel(PET_PICS_CHANNEL)
    await channel.send(
        "Daily Dose of Sauce! Enjoy This Pic Of Me, My Friends, And/Or Their Humans! Have A Great Day",
        file=discord.File(local_fp))
    os.remove(local_fp)


def is_match_database(key, val):
    conn = psycopg2.connect(**DATABASE_INFO)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("select * from discord where key = %s", (key,))
    res = cur.fetchone()
    if res:
        i, dbkey, dbval = res
        if dbval == val:
            conn.close()
            return True
        cur.execute("update discord set value = %s where id = %s", (val, i))
    else:
        print("Couldn't Find [{}] in DB".format(key))
    conn.close()
    return False

def check_youtube(channel_id, db_key):
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

@tasks.loop(minutes=30)
async def send_daily_apex_update():

    async def crafting_update():
        r = requests.get("https://api.mozambiquehe.re/crafting?auth={}".format(APEX_TOKEN))
        files = []
        for item in r.json():
            if "start" in item:
                content = item['bundleContent']
                for i in content:
                    asset = i['itemType']['asset']
                    basename = os.path.basename(asset)
                    r = requests.get(asset, stream = True)
        
                    if r.status_code == 200:
                        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                        r.raw.decode_content = True
                        # Open a local file with wb ( write binary ) permission.
                        with open(basename,'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                        files.append(basename)
        key = "".join(files)
        if is_match_database('apex_rotation', key):
            return
    
        template_main = Image.open("res/template.png")
        template = template_main.copy()
        starting_point = (5,35)
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
        uploaded_img = imgur.upload_from_path(filename, anon=False)
        album = imgur.get_album(IMGUR_ALBUM_ID)
        imgur.delete_image(album.images[0]['id'])
        imgur.album_add_images(IMGUR_ALBUM_ID, [uploaded_img['id']])
    
        tz = pytz.timezone("US/Pacific")
        date = datetime.strftime(datetime.now(tz), "%m-%d/%Y %-I:%M%p")
        embed = discord.Embed(
                title='APEX: Daily Crafting Rotation',
                description=date,
                colour=discord.Colour.red()
                )
        embed.set_image(url=uploaded_img['link'])
        channel = bot.get_channel(APEX_CHANNEL)
        await channel.send(embed=embed)
        os.remove(filename)
        for f in files:
            os.remove(f)

    await crafting_update()
    url = check_youtube("playapex", "apex_last_video")
    if url:
        channel = bot.get_channel(APEX_CHANNEL)
        await channel.send("New Upload From ApexLegends!\n{}".format(url))

@tasks.loop(minutes=30)
async def send_daily_ow_update():
    url = check_youtube("playoverwatch", "ow_last_video")
    if url:
        channel = bot.get_channel(OW_CHANNEL)
        await channel.send("New Upload From PlayOverwatch!\n{}".format(url))

@send_daily_messages.before_loop
async def before_msg1():
    tz = pytz.timezone("US/Pacific")
    while True:
        if datetime.now(tz).hour == 10:
            return
        await asyncio.sleep(60)


# Send FAQ Guidance
@bot.event
async def on_member_join(member):
    """
    On member join event
    Called whenever someone joins server

    :param member: Member object of joining user
    """
    welcome_channel = bot.get_channel(WELCOME_CHANNEL)
    readme_channel = bot.get_channel(READ_ME_CHANNEL)
    msg = "What's up {0}! Welcome to Noc's Corner. Check out the {1}".format(
        member.mention, readme_channel.mention)
    embed = discord.Embed(title="{0} just joined the server!".format(
        member.display_name), color=0x03ecfc)
    embed.set_thumbnail(url=member.avatar_url)
    await welcome_channel.send(msg, embed=embed)


# Live Streamers Role
async def _live_streamers(member):
    """
    Private method to handle live streamers role assign logic.
    Will assign a live streamers role to anyone currently streaming

    :param member: Currently updated member object
    """
    def get_streamer_activity(acts):
        """
        Takes list of activities and returns the streamer activity

        :param acts: tuple of activities

        :return: activity if found else None
        """
        activities = list(acts)
        for a in activities:
            if a.type == discord.ActivityType.streaming:
                return a

    # Check if role is higher than threshold for live streamer status
    role_min = discord.utils.get(member.guild.roles, name=LIVE_STREAMERS_ROLE_MINIMUM)
    if role_min and role_min > member.top_role:
        return

    # Get live streamers role
    role = discord.utils.get(member.guild.roles, name=LIVE_STREAMERS)
    if not role:
        return

    # Check if member is currently streaming + has streamer role
    activity = get_streamer_activity(member.activities)
    if activity and role not in member.roles:
        channel = bot.get_channel(STREAMER_CHANNEL)
        await member.add_roles(role)

        # check if member stream has already been started recently
        if member.name in ACTIVE_STREAMERS and ACTIVE_STREAMERS[member.name].is_active():
            return

        await channel.send("{0} is now streaming: [{1}: {2}]. Tune in!".format(
            member.mention, activity.game, activity.name))
    elif not activity and role in member.roles:
        # stream has ended, remove role and start timer in case comes back online
        await member.remove_roles(role)
        timer = Timer()
        timer.start(60)
        ACTIVE_STREAMERS[member.name] = timer


@bot.event
async def on_member_update(before, after):
    """
    On member update event. Will be called everytime a member is updated

    :param before: before member object
    :param after: after member object
    """
    await _live_streamers(after)


# Role Select
@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    ctx = await bot.get_context(msg)
    member = discord.utils.find(lambda m: m.id == payload.user_id, ctx.guild.members)

    if msg.id != ROLE_REACT_MESSAGE_ID:
        return

    role_name = payload.emoji.name.lower()
    for role in ctx.guild.roles:
        if role_name in role.name.lower():
            await member.remove_roles(role)
            break


@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    ctx = await bot.get_context(msg)
    member = discord.utils.find(lambda m: m.id == payload.user_id, ctx.guild.members)

    if msg.id != ROLE_REACT_MESSAGE_ID:
        return

    role_name = payload.emoji.name.lower()
    for role in ctx.guild.roles:
        if role_name in role.name.lower():
            await member.add_roles(role)
            break
    else:
        if role_name != "🚫":
            await msg.remove_reaction(payload.emoji, member)

    base_role = discord.utils.get(ctx.guild.roles, name=BASE_ROLE_NAME)
    if base_role not in member.roles:
        await member.add_roles(base_role)


# Start BOT
bot.run(DISCORD_TOKEN)
