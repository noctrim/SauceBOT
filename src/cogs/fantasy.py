import discord
from discord.ext import commands

from .base import CogBase

class FantasyFootball(CogBase):
    # Fantasy Football Cog

    @commands.slash_command(name="total_wins", description="See total wins for all players since any given season.")
    async def total_wins(ctx, year):
        if not year.isnumeric():
            await ctx.respond("Invalid input, try a year. Ex: 2022")
            return
        year = int(year)
        embed = discord.Embed(
                title=f'Wins Since {year} Season',
                colour=discord.Colour.red()
                )
        filename = generate_wins_bar_graph(year)
        file_ = discord.File(filename)
        embed.set_image(url="attachment://{}".format(filename))
        await ctx.respond(file=file_, embed=embed)
        os.remove(filename)
