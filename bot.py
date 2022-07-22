import discord
import os

from discord.ext import commands

from src.cogs.daily import DailyUpdates
from src.cogs.roles import Roles

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

WELCOME_CHANNEL = 963877676551118909
READ_ME_CHANNEL = 963877448221593680

COMMAND_OPT = "!"


intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(intents=intents, command_prefix=COMMAND_OPT)
for cog in [DailyUpdates, Roles]:
    bot.add_cog(cog(bot))


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
    cog = bot.get_cog("DailyUpdates")
    cog.send_daily_messages.start()


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


# Start BOT
bot.run(DISCORD_TOKEN)
