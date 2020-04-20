
import discord
import os
import random
import re
import requests
import pyimgur

TOKEN = os.environ["DISCORD_TOKEN"]
IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
IMGUR_ALBUM_ID = "XNDQTsC"

client = discord.Client()
imgur = pyimgur.Imgur(IMGUR_CLIENT_ID)

class Emoji(object):
    def __init__(self, text):
        r = re.match(r'(?:\<:([^:]+):([0-9]+)\>)', text)
        if not r:
            self.value = text
            return
        emojis = list(filter(lambda e: str(e.id) == r.group(2), client.emojis))
        self.value = emojis[0].name

def get_mapping(text):
    mapping = {}
    r = re.search(r'\[([\s\S]*)\]', text)
    if not r:
        return mapping
    input_map = r.group(1).strip()
    for line in input_map.splitlines():
        try:
            emoji, role = line.split("-")
            role = role.strip()
            if not any([emoji, role]):
                break
            emoji = Emoji(emoji.strip())
            mapping[emoji.value] = role
        except Exception as e:
            break
    return mapping

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

        mapping = get_mapping(text)
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

        mapping = get_mapping(text)
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

def download_file(url, name='tmp.jpg'):
    resp = requests.get(url)
    if resp.status_code == 200:
        print("Response Recieved. Downloading File: {0}".format(url))
        with open(name, 'wb') as f:
            f.write(resp.content)
            f.close()
            return name
    else:
        print("Error Code: {0} Downloading File: {1}".format(resp.status_code, url)) 

SAUCE_KEYWORDS = ["game", "play"]
SAUCE_OPTIONS = ["I love to play!", "", "PICK ME!!", "I mean I'm down for some fetch"]

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    text_lower = message.content.lower()
    if any(x in text_lower for x in SAUCE_KEYWORDS):
        msg = "Bork! BORK! {0}".format(random.choice(SAUCE_OPTIONS))
        album = imgur.get_album(IMGUR_ALBUM_ID)
        image = random.choice(album.images)
        path = download_file(image.link)
        if path:
            file = discord.File(path)
            await message.channel.send(msg, file=file)
            os.remove(path)


"""
@client.event
async def on_member_join(member):
    server = member.guild
    channel = server.system_channel
    await channel.send("Welcome {0}!".format(member.mention))
"""
client.run(TOKEN)