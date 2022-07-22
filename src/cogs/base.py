from discord.ext import commands


class CogBase(commands.Cog):
    """
    Base class for all Cogs to handle shared setup
    """
    def __init__(self, bot):
        self.bot = bot
