import discord
import os
from discord.ext import commands

from .base import CogBase
from ..libs.espn import generate_wins_bar_graph


class FantasyFootball(CogBase):
    # Fantasy Football Cog

    @commands.slash_command(name="total_wins", description="See total wins for all players since any given season.")
    async def total_wins(self, ctx, year):
        try:
            year = int(year)
        except ValueError:
            await ctx.respond("Invalid input, try a year. Ex: 2022")
            return
        if year < 2018:
            await ctx.respond("Data only supports since 2018+ season")
            return
        embed = discord.Embed(
                title=f'Wins Since {year} Season',
                colour=discord.Colour.red()
                )
        filename = generate_wins_bar_graph(year)
        file_ = discord.File(filename)
        embed.set_image(url="attachment://{}".format(filename))
        await ctx.respond(file=file_, embed=embed)
        os.remove(filename)
