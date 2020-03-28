import discord
import os

TOKEN = os.environ["DISCORD_TOKEN"]

client = discord.Client()
message_id = 693534132621279307

emoji_mapping = {
    "Apex": "Apex",
    "WorldOfWarcraft": "WoW",
    "Overwatch": "Overwatch",
    "LeagueOfLegends": "League"
}

@client.event
async def on_raw_reaction_add(payload):
    """
    Adds role on emoji reaction
    :param payload: discord payload item
    """
    # Check if current message reacted too is set message
    if payload.message_id == message_id:
        guild = discord.utils.find(lambda g: g.id == payload.guild_id, client.guilds)
        role = discord.utils.get(guild.roles, name=emoji_mapping.get(payload.emoji.name, None))
        
        # If reacted emoji matches role, grant access
        if role is not None:
            member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
            await member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    """
    Adds role on emoji reaction
    :param payload: discord payload item
    """
    # Check if current message reacted too is set message
    if payload.message_id == message_id:
        guild = discord.utils.find(lambda g: g.id == payload.guild_id, client.guilds)
        role = discord.utils.get(guild.roles, name=emoji_mapping.get(payload.emoji.name, None))

        # If reacted emoji matches role, grant access
        if role is not None:
            member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
            await member.remove_roles(role)

"""
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await message.channel.send(msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_member_join(member):
    server = member.guild
    channel = server.system_channel
    await channel.send("Welcome {0}!".format(member.mention))
"""
client.run(TOKEN)