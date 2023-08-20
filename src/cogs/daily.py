from datetime import datetime
from discord.ext import tasks
import random
import asyncio
import discord
import os
import pytz

from .base import CogBase
from ..libs.apex import generate_crafting_image
from ..libs.database import (
    add_photo_to_table, clear_table, get_all_seen_photos, get_config, get_database, is_match_database)
from ..libs.s3 import get_all_relevant_photos, download_file
from ..libs.youtube import check_youtube
from ..libs.espn import generate_matchups_image


DAILY_MESSAGE_HOUR = 10
DAILY_MESSAGE_TZ = pytz.timezone("US/Pacific")


class DailyUpdates(CogBase):
    # Send Daily Dog Photo To Channel
    async def send_daily_messages(self):
        """
        Task that loops every 24 hours to send daily messages
        """
        # In case BOT is restarted, this will wait for next increment
        # Otherwise BOT messages will start 24 hours from online
        self.send_daily_apex_update.start()
        self.send_daily_ow_update.start()
        self.send_daily_wow_update.start()
        while True:
            if datetime.now(DAILY_MESSAGE_TZ).hour == DAILY_MESSAGE_HOUR:
                break
            await asyncio.sleep(60)
        self.send_daily_photo.start()
        self.send_daily_espn_update.start()

    @tasks.loop(hours=24)
    async def send_daily_photo(self):
        """
        Helper util function to send daily sauce photo
        """
        photos = get_all_relevant_photos()
        random.shuffle(photos)
        avail_photos = set(photos)
        seen_photos = set(get_all_seen_photos())

        not_posted = avail_photos - seen_photos
        try:
            photo = not_posted.pop()
        except KeyError:
            clear_table()
            photo = avail_photos.pop()
        add_photo_to_table(photo)
        local_fp = "temp.png"
        download_file(photo, local_fp)

        for guild in self.bot.guilds:
            pet_pics_channel = get_config(guild.id, "petPicsChannel")
            if not pet_pics_channel:
                continue
            channel = self.bot.get_channel(pet_pics_channel)
            await channel.send(
                "Daily Dose of Sauce! Enjoy This Pic Of Me, My Friends, And/Or Their Humans! Have A Great Day",
                file=discord.File(local_fp))
        os.remove(local_fp)

    @tasks.loop(hours=24)
    async def send_daily_espn_update(self):
        if datetime.now(DAILY_MESSAGE_TZ).weekday() == 1:
            filename = generate_matchups_image()
            if filename:
                channel = self.bot.get_channel(1142584475256111155)
                embed = discord.Embed(
                        title=f'Main Events of the Week',
                        colour=discord.Colour.red()
                        )
                file_ = discord.File(filename)
                embed.set_image(url="attachment://{}".format(filename))
                await channel.send(file=file_, embed=embed)
                os.remove(filename)

    async def youtube_update(self, youtube_channel, db_key, send_channel, youtube_display=None):
        """
        Helper function to check if a youtube channel has posted a new video

        :param youtube_channel: name of youtube channel to check
        :param db_key: key in DB where last seen video is stored
        :param send_channel: discord channel to send update
        :param youtube_display: override for channel name if different than expected display
        """
        url = check_youtube(youtube_channel.lower(), db_key)
        if url:
            channel = self.bot.get_channel(send_channel)
            name = youtube_display or youtube_channel
            await channel.send("New Upload From {0}!\n{1}".format(name, url))

    # [SECTION] Apex
    @tasks.loop(minutes=30)
    async def send_daily_apex_update(self):
        """
        Task to send live Apex updates
        """
        filename = generate_crafting_image()
        if not filename:
            return

        date = datetime.strftime(datetime.now(DAILY_MESSAGE_TZ), "%m-%d/%Y %-I:%M%p")
        embed = discord.Embed(
                title='APEX: Daily Crafting Rotation',
                description=date,
                colour=discord.Colour.red()
                )

        file_ = discord.File(filename)
        embed.set_image(url="attachment://{}".format(filename))

        for guild in self.bot.guilds:
            apex_channel = get_config(guild.id, "apexChannel")
            if not apex_channel:
                continue
            await self.youtube_update("playapex", "apex_last_video", apex_channel, "ApexLegends")
            if embed:
                channel = self.bot.get_channel(apex_channel)
                await channel.send(file=file_, embed=embed)
        os.remove(filename)

    # [SECTION] Overwatch
    @tasks.loop(minutes=30)
    async def send_daily_ow_update(self):
        """
        Task to send live overwatch updates
        """
        for guild in self.bot.guilds:
            ow_channel = get_config(guild.id, "owChannel")
            if not ow_channel:
                continue
            await self.youtube_update("PlayOverwatch", "ow_last_video", ow_channel)

    # [SECTION] World of Warcraft
    @tasks.loop(minutes=10)
    async def send_daily_wow_update(self):
        """
        Task to send live WoW updates
        """
        if is_match_database("skyfury_queue", "0", update=False):
            game = discord.Game("Fetch!")
        else:
            queue = get_database("skyfury_queue")
            game = discord.Game(queue)
        await self.bot.change_presence(status=discord.Status.idle, activity=game)
