import discord
import os
import random
import re
import time

from src.emoji import Emoji
from src.imgur import ImgurBehavior
from src.timer import Timer

TOKEN = os.environ["DISCORD_TOKEN"]

client = discord.Client()
imgur = ImgurBehavior()


@client.event
async def on_raw_reaction_add(payload):
    """
    Adds role on emoji reaction
    :param payload: discord payload item
    """
    # Check if current message reacted too is set message
    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    if "!role-select" in msg.content and msg.author.top_role.permissions.administrator:
        _, text = msg.content.split("!role-select")
        text = text.strip()

        mapping = Emoji.get_mapping(text, client.emojis)
        role_name = mapping.get(payload.emoji.name, None)
        guild = discord.utils.find(lambda g: g.id == payload.guild_id, client.guilds)
        role = discord.utils.get(guild.roles, name=role_name)
        member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)

        # If reacted emoji matches role, grant access
        if role is not None:
            await member.add_roles(role)
        elif role_name is not None:
            role = await guild.create_role(name=role_name, reason="Select Role BOT")
            await member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    """
    Adds role on emoji reaction
    :param payload: discord payload item
    """
    # Check if current message reacted too is set message
    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    if "!role-select" in msg.content and msg.author.top_role.permissions.administrator:
        _, text = msg.content.split("!role-select")
        text = text.strip()

        mapping = Emoji.get_mapping(text, client.emojis)
        role_name = mapping.get(payload.emoji.name, None)
        guild = discord.utils.find(lambda g: g.id == payload.guild_id, client.guilds)
        role = discord.utils.get(guild.roles, name=role_name)
        member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)

        # If reacted emoji matches role, grant access
        if role is not None:
            await member.remove_roles(role)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    game = discord.Game("Fetch!")
    await client.change_presence(status=discord.Status.idle, activity=game)


SAUCE_KEYWORDS = ["game", "play"]
SAUCE_OPTIONS = ["I love to play!", "", "PICK ME!!", "I mean I'm down for some fetch"]

timer = Timer(30)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user or message.author.bot:
        return
    text_lower = message.content.lower()
    if "sauce stop" in text_lower:
        timer.start()
    if timer.is_active():
        return
    r = r'(^|.)({0})'.format('|'.join(SAUCE_KEYWORDS))
    if any([c != "!" for c, v in re.findall(r, text_lower)]):
        msg = "Bork! BORK! {0}".format(random.choice(SAUCE_OPTIONS))
        album = imgur.get_album()
        image = random.choice(album.images)
        path = imgur.download_file(image.link)
        if path:
            file = discord.File(path)
            await message.channel.send(msg, file=file)
            os.remove(path)

client.run(TOKEN)
