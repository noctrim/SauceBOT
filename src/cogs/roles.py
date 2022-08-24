from discord.ext import commands
import discord

from .base import CogBase
from ..libs.database import get_config
from ..libs.timer import Timer


ACTIVE_STREAMERS = {}
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
        ctx = await self.bot.get_context(msg)

        role_react_message = get_config(ctx.guild.id, "roleReact")
        if msg.id != role_react_message:
            return

        member = discord.utils.find(lambda m: m.id == payload.user_id, ctx.guild.members)

        # add base role if missing
        base_role_id = get_config(ctx.guild.id, "baseRole")
        if base_role_id:
            base_role = discord.utils.get(ctx.guild.roles, id=base_role_id)
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

        # Get live streamers role
        live_streamers_role = get_config(member.guild.id, "liveStreamerRole")
        if not live_streamers_role:
            return

        role = discord.utils.get(member.guild.roles, name=live_streamers_role)
        if not role:
            return

        # Check if role is higher than threshold for live streamer status
        live_streamers_role_min = get_config(member.guild.id, "liveStreamerRoleMinimum")
        if live_streamers_role_min:
            role_min = discord.utils.get(member.guild.roles, name=live_streamers_role_min)
            if role_min and role_min > member.top_role:
                return

        # Check if member is currently streaming + has streamer role
        streamer_channel = get_config(member.guild.id, "streamerChannel")
        activity = get_streamer_activity(member.activities)
        if activity and role not in member.roles:
            await member.add_roles(role)

            # check if member stream has already been started recently
            if member.name in ACTIVE_STREAMERS and ACTIVE_STREAMERS[member.name].is_active():
                return
            if streamer_channel:
                channel = self.bot.get_channel(streamer_channel)
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
