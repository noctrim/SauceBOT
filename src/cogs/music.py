import asyncio
import discord

from collections import defaultdict
from discord.ext import commands
from discord.ui import Button, View
from functools import partial

from .base import CogBase
from ..libs.timer import Timer
from ..libs.youtube import get_song_iterator, get_stream


class Music(CogBase):
    # Control Music Playback

    QUEUE = defaultdict(list)

    @commands.command()
    async def join(self, ctx):
        """
        Connects BOT to server
        """
        if ctx.author.voice is None:
            return None
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        return ctx.voice_client

    @commands.slash_command(name="pause", description="Pause the currently playing song")
    async def pause(self, ctx):
        """
        Pauses current voice playback
        """
        vc = ctx.voice_client
        if not vc:
            await ctx.respond("Nothing playing to pause")
        elif vc.is_paused():
            await ctx.respond("Music already paused")
        else:
            ctx.voice_client.pause()
            await ctx.respond("Paused")

    @commands.slash_command(name="resume", description="Resume playback of paused song")
    async def resume(self, ctx):
        """
        Resumes current voice playback
        """
        vc = ctx.voice_client
        if not vc:
            await ctx.respond("Nothing playing to resume")
        elif not vc.is_paused():
            await ctx.respond("Music isn't paused")
        else:
            vc.resume()
            await ctx.respond("Resumed")

    @commands.slash_command(name="skip", description="Skip current song in queue")
    async def skip(self, ctx):
        """
        Skips current song
        """
        vc = ctx.voice_client
        if not vc:
            await ctx.respond("Nothing playing to skip")
        else:
            ctx.voice_client.stop()
            await ctx.respond("Skipped")

    async def handle_audio(self, queue, vc, url):
        """
        Helper function to play a song queue
        """
        # Wait for current songs turn
        while True:
            if not queue:
                break
            song = queue.pop(0)
            # start playback
            source = await get_stream(song)
            vc.play(source)

            # wait for playback to complete
            pause_timer = Timer()
            while vc.is_playing() or vc.is_paused():
                if vc.is_paused() and not pause_timer.started:
                    pause_timer.start(60 * 2)
                if pause_timer.started and not pause_timer.is_active():
                    await vc.disconnect()
                    queue.clear()
                    return
                await asyncio.sleep(2)
        await vc.disconnect()

    @commands.slash_command(name="play", description="Play a song or title from youtube video")
    async def play(self, ctx, title):
        """
        Command to play a song by given title
        """
        songs_iterator = get_song_iterator(title)
        items = next(songs_iterator)

        async def _play(chosen, interaction):
            picked_song = items[chosen]
            title = picked_song['snippet']['title']
            queue = self.QUEUE[interaction.guild_id]
            url = "www.youtube.com/watch?v={}".format(picked_song['id']['videoId'])
            if queue:
                msg = "**Added:** *{}* to the queue!".format(title)
                queue.append(url)
                await interaction.response.send_message(content=msg, view=None)
            else:
                msg = "**Now Playing:** *{}* Enjoy!".format(title)
                vc = await self.join(ctx)
                if vc:
                    queue.append(url)
                    await interaction.response.send_message(content=msg, view=None)
                    await self.handle_audio(queue, vc, url)
                else:
                    await interaction.response.send_message(content="You are not in a voice channel!", view=None)

        def build_message():
            """
            Helper function to build sent message
            """
            async def cancel(inter):
                await inter.response.send_message(content="Canceled", view=None)

            view = View()
            lines = ["Please select a track from below"]
            for i, item in enumerate(items):
                line = "{0}: {1}".format(i+1, item['snippet']['title'])
                lines.append(line)
                button = Button(label=str(i+1), style=discord.ButtonStyle.blurple)
                button.callback = partial(_play, i)
                view.add_item(button)
            msg = "\n".join(lines)

            button = Button(emoji="🚫")
            button.callback = cancel
            view.add_item(button)
            return msg, view

        msg, view = build_message()
        await ctx.send(msg, view=view)
