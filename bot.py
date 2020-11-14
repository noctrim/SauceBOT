import discord
import os
import random
import re

from discord.ext import commands
from src.imgur import ImgurBehavior
from src.timer import Timer

TOKEN = os.environ["DISCORD_TOKEN"]

imgur = ImgurBehavior()

ANNOUNCEMENTS_CHANNEL = 417857966213955584
IMGUR_ALBUM_ID = "XNDQTsC"
COMMAND_OPT = "!"
ROLE_SELECT = COMMAND_OPT + "role-select"
LIVE_STREAMERS = "Live Streamers"
LIVE_STREAMERS_ROLE_MINIMUM = "Wolf Pack"
STREAMER_CHANNEL = 730792934055608411
STREAMER_ID = 197958875171913728
STREAMER_MESSAGE = "Going LIVE! @everyone tune in https://www.twitch.tv/jkrout"
SAUCE_STOP = "sauce stop"
SAUCE_KEYWORDS = ["game", "play"]
SAUCE_OPTIONS = ["I love to play!", "", "PICK ME!!", "I mean I'm down for some fetch"]
SAUCE_MESSAGE_PREFIX = "Bork! BORK!"
SAUCE_SLEEP_TIME = 30
TIMER = Timer(SAUCE_SLEEP_TIME)
WELCOME_CHANNEL = 693574297809059851

intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(intents=intents, command_prefix=COMMAND_OPT)
emoji_converter = commands.EmojiConverter()


async def _get_emoji_mapping(ctx):
    """
    Reads ctx and returns dictionary mapping of emoji-role for role select

    :param ctx: Discord context

    :return: dictionary of emoji mapping
    """
    mapping = {}

    # Grab text after key
    _, text = ctx.message.content.split(ROLE_SELECT)
    text = text.strip()

    # Grab text between brackets
    r = re.search(r'\[([\s\S]*)\]', text)
    if not r:
        print("Check formatting for role select message")
        return mapping
    input_map = r.group(1).strip()

    # Get mapping of emoji- role name
    lines = input_map.splitlines()
    for line in lines:
        try:
            emoji, role = line.split("-")
            emoji = emoji.strip()
            # if is custom emoji convert will return value
            # otherwise emoji is standard emoji
            temp = await emoji_converter.convert(ctx, emoji)
            emoji_name = temp.name if temp else emoji
            mapping[emoji_name] = role.strip()
        except Exception as e:
            print("Error: {0}\n Parsing role select line: {1}. Check formatting.".format(e, line))
            continue
    return mapping


async def _role_select(msg, payload, added=True):
    """
    Private method to handle the logic for role select feature.
    Role select will use a message in the form of
    <ROLE_SELECT_KEY>[
        <ROLE_1>: <EMOJI_1>
        <ROLE_2>: <EMOJI_2>
    ]
    then add/remove the role based on the associated emoji reaction

    :param msg: main message
    :param payload: reaction payload
    :param added: boolean to track whether emoji was added or removed

    :return: (role, member) associated discord role object (or None if doesn't exist) and current member
    """
    # Check if role select keyword is inside message and the message sender has admin role
    if ROLE_SELECT not in msg.content or not msg.author.top_role.permissions.administrator:
        return

    # Parse text for role to emoji mapping
    ctx = await bot.get_context(msg)
    mapping = await _get_emoji_mapping(ctx)

    # Get expected role name from reacted emoji
    role_name = mapping.get(payload.emoji.name, None)
    if not role_name:
        # reacted emoji is not inside mapping
        return

    # Try to find existing role from emoji name
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    # Get current member object
    member = discord.utils.find(lambda m: m.id == payload.user_id, ctx.guild.members)

    if added:
        # If no role exists already for current mapped emoji create one
        if not role:
            role = await ctx.guild.create_role(name=role_name, reason="[SauceBOT] Select Role")
        # Add role to member
        await member.add_roles(role)
    else:
        # Remove reacted role if user has it
        if role:
            await member.remove_roles(role)


@bot.event
async def on_raw_reaction_add(payload):
    """
    On raw reaction add event
    Called whenever any message has a reaction added from it on server

    :param payload: discord payload item
    """

    # Get reacted message
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)

    # Do any checks on msg
    await _role_select(msg, payload, added=True)


@bot.event
async def on_raw_reaction_remove(payload):
    """
    On raw reaction remove event
    Called whenever any message has a reaction removed from it on server

    :param payload: discord payload item
    """

    # Get reacted message
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)

    # Do any checks on msg
    await _role_select(msg, payload, added=False)


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


@bot.event
async def on_member_join(member):
    """
    On member join event
    Called whenever someone joins server

    :param member: Member object of joining user
    """
    welcome_channel = bot.get_channel(WELCOME_CHANNEL)
    msg = "What's up {0}! Check out the {1} channel!".format(
        member.mention, welcome_channel.mention)
    embed = discord.Embed(title="{0} just joined the server!".format(
        member.display_name), color=0x03ecfc)
    embed.set_thumbnail(url=member.avatar_url)

    announcements_channel = bot.get_channel(ANNOUNCEMENTS_CHANNEL)
    await announcements_channel.send(msg, embed=embed)


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

    # Add / Remove role if needed
    activity = get_streamer_activity(member.activities)
    if activity and role not in member.roles:
        if member.id == STREAMER_ID:
            channel = bot.get_channel(STREAMER_CHANNEL)
            await channel.send("{0} is playing {1}: {2}\n@everyone tune in now! https://www.twitch.tv/jkrout".format(
                member.mention, activity.game, activity.name))
        await member.add_roles(role)
    elif not activity and role in member.roles:
        await member.remove_roles(role)


@bot.event
async def on_member_update(before, after):
    """
    On member update event. Will be called everytime a member is updated

    :param before: before member object
    :param after: after member object
    """
    await _live_streamers(after)


async def _send_image_if_keyword(message):
    """
    Private method to handle fun sauce BOT imgur responses

    :param message: discord message received
    """

    # Turn keywords into regex
    keyword_regex = r'(^|.)({0})'.format('|'.join(SAUCE_KEYWORDS))

    # Get text
    text = message.content

    # Search text for any keyword that is not proceeded by !
    # Prevents people from using !play with music BOT and receiving response
    if any([c != "!" for c, v in re.findall(keyword_regex, text.lower())]):
        # Create message text
        prefix = SAUCE_MESSAGE_PREFIX + " " if SAUCE_MESSAGE_PREFIX else ""
        msg = "{0}{1}".format(prefix, random.choice(SAUCE_OPTIONS))

        # Get random img from album
        album = imgur.get_album(IMGUR_ALBUM_ID)
        image = random.choice(album.images)

        # Download image
        path = imgur.download_file(image.link)
        if path:
            # Attach image to file and send message
            file = discord.File(path)
            await message.channel.send(msg, file=file)
            # cleanup file
            os.remove(path)


@bot.event
async def on_message(message):
    """
    On message received event
    Called whenever server receives any message

    :param message: message received from server
    """
    # we do not want the bot to reply to itself
    if message.author == bot.user or message.author.bot:
        return

    text = message.content

    # sets sleep timer if message received
    if SAUCE_STOP.lower() in text.lower():
        TIMER.start()

    # if timer is active exit
    if TIMER.is_active():
        return

    # check for keyword and send imgur item
    await _send_image_if_keyword(message)


# Start BOT
bot.run(TOKEN)
