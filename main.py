import os
import re
from urllib.parse import quote

import discord
from discord.ext import commands

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is required")

WIKI = "https://scrooms.miraheze.org/wiki/"
WIKILINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
ALLOWED_ROLES = {"Helper"}
OPEN_CHANNELS = {"bot-commands", "questions", "trash-can"}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def wiki_url(title):
    page = title.split("|", 1)[0].strip().replace(" ", "_")
    if not page:
        return None
    return WIKI + quote(page, safe="/:_-'()")


def is_allowed(message):
    if not isinstance(message.author, discord.Member):
        return False

    channel = message.channel
    names = {getattr(channel, "name", None)}
    parent = getattr(channel, "parent", None)
    if parent is not None:
        names.add(getattr(parent, "name", None))
    if names & OPEN_CHANNELS:
        return True

    role_names = {role.name for role in message.author.roles}
    return bool(role_names & ALLOWED_ROLES)


@bot.event
async def on_ready():
    print(f"Connected as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot or not is_allowed(message):
        return

    urls = []
    for title in WIKILINK.findall(message.content):
        url = wiki_url(title)
        if url and url not in urls:
            urls.append(url)
        if len(urls) == 3:
            break

    if urls:
        await message.channel.send("\n".join(urls))

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Command usage: [[title]]")
        return
    raise error


bot.run(token)