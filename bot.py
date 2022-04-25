import asyncio
import boto3
import discord
import os
import pytz
import random

from datetime import datetime
from discord.ext import commands, tasks

from src.timer import Timer

TOKEN = os.environ["DISCORD_TOKEN"]

TIMER = Timer()
STREAMER_TIMER = Timer()
ACTIVE_STREAMERS = {}

ANNOUNCEMENTS_CHANNEL = 963877676551118909
PET_PICS_CHANNEL = 967919501037437018
STREAMER_CHANNEL = 967914669576712222
WELCOME_CHANNEL = 963877448221593680

ROLE_REACT_MESSAGE_ID = 967193372588638218

COMMAND_OPT = "!"

BASE_ROLE_NAME = "Benchwarmer"
LIVE_STREAMERS = "Live"
LIVE_STREAMERS_ROLE_MINIMUM = "ANBU Black Ops"
STREAMING_CHANNEL_NOTIFICATION_DELAY = 60

AWS_KEY = os.environ["AWS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]
session = boto3.Session(aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
s3 = session.resource('s3')
s3_bucket = s3.Bucket("noctrimphotos")
SENT_PHOTOS = set()

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

    send_daily_photo.start()


# Send Daily Dog Photo To Channel
@tasks.loop(hours=24)
async def send_daily_photo():
    avail_photos = [f for f in s3_bucket.objects.all() if not f.endswith("/")]
    random.shuffle(avail_photos)
    for photo in avail_photos:
        if photo not in SENT_PHOTOS:
            SENT_PHOTOS.add(photo)
            break
    else:
        # All photos were seen, clear and start over
        SENT_PHOTOS.clear()
        SENT_PHOTOS.add(photo)

    local_fp = "temp.png"
    s3_bucket.download_file(photo, local_fp)

    channel = bot.get_channel(PET_PICS_CHANNEL)
    await channel.send(
        "Daily Dose of Sauce! Enjoy This Pic Of Me, My Friends, And/Or Their Humans! Have A Great Day",
        file=local_fp)
    os.remove(local_fp)


@send_daily_photo.before_loop
async def before_msg1():
    tz = pytz.timezone("US/Pacific")
    while True:
        if datetime.now(tz).hour == 9:
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
    msg = "What's up {0}! Welcome to Noc's Corner. Check out the {1}".format(
        member.mention, welcome_channel.mention)
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
bot.run(TOKEN)
