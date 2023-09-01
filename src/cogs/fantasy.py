import discord
import os
from discord.ext import commands

from .base import CogBase
from ..libs.espn import generate_wins_bar_graph, get_record_players, OWNER_MAPPING


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

    @commands.slash_command(name="rec_against", description="See record against player since any given season.")
    async def record_against(self, ctx, firstplayer, secondplayer, year):
        try:
            year = int(year)
        except ValueError:
            await ctx.respond(f"Invalid input: [{year}], try a year. Ex: 2022")
            return
        if year < 2018:
            await ctx.respond(f"Data only supports since 2018+ season (Invalid: {year})")
            return
        players = [k.lower() for k in OWNER_MAPPING.values()]
        for p in [firstplayer, secondplayer]:
            if p.lower() not in players:
                await ctx.respond(f"Invalid input: [{p}]. Allowable players: {players}")
                return

        record = get_record_players(firstplayer, secondplayer, year)
        msg = ""
        for player, (total, playoff) in record.items():
            msg += f"{player} won {total} time{'s' if total != 1 else ''}"
            if playoff > 0:
                msg += f' with {playoff} being in playoffs'
            msg += '\n'
        embed = discord.Embed(
                title=f'Record Since {year} Season',
                description=msg,
                colour=discord.Colour.red()
                )
        await ctx.respond('', embed=embed)
