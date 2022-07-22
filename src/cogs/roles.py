import discord

from .base import CogBase
from discord.ext import commands
from ..libs.timer import Timer

ROLE_REACT_MESSAGE_ID = 967193372588638218
STREAMER_CHANNEL = 967914669576712222

ACTIVE_STREAMERS = {}
BASE_ROLE_NAME = "Squad"
LIVE_STREAMERS = "Live"
LIVE_STREAMERS_ROLE_MINIMUM = "ANBU Black Ops"
STREAMING_CHANNEL_NOTIFICATION_DELAY = 60


class Roles(CogBase):
    """
    Cog for handling any role manipulation

    Current Features:
        - Role Select by Reaction
        - Live Streamer role when Live
    """
    # [SECTION] Role Select
    async def _role_select(self, payload, add=True):
        """
        Helper function to handle role select by reaction for both add/remove cases

        :param payload: discord payload obj
        :param add: bool to flag add or remove
        """
        # check if event was reaction to role message
        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        if msg.id != ROLE_REACT_MESSAGE_ID:
            return

        ctx = await self.bot.get_context(msg)
        member = discord.utils.find(lambda m: m.id == payload.user_id, ctx.guild.members)

        # add base role if missing
        base_role = discord.utils.get(ctx.guild.roles, name=BASE_ROLE_NAME)
        if base_role not in member.roles:
            await member.add_roles(base_role)

        expected_role_name = payload.emoji.name.lower()
        # check for opt out
        if expected_role_name == "🚫":
            return

        # look for matching role
        for role in ctx.guild.roles:
            if expected_role_name in role.name.lower():
                if add:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
                break
        else:
            await msg.remove_reaction(payload.emoji, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Listener function for reaction removal

        :param payload: discord payload obj
        """
        await self._role_select(payload, add=False)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Listener function for reaction add

        :param payload: discord payload obj
        """
        await self._role_select(payload)

    # [SECTION] Live Streamers Role
    async def _live_streamers(self, member):
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
            channel = self.bot.get_channel(STREAMER_CHANNEL)
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

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        Listener function for on member update event.

        :param before: before member object
        :param after: after member object
        """
        await self._live_streamers(after)
