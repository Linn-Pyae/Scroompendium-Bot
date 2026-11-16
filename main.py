import os
import re
from urllib.parse import quote

import aiohttp
import discord
from discord.ext import commands

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is required")

WIKI = "https://scrooms.miraheze.org/wiki/"
API = "https://scrooms.miraheze.org/w/api.php"
WIKILINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
ALLOWED_ROLES = {"Helper"}
OPEN_CHANNELS = {"bot-commands", "questions", "trash-can"}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def page_name(title):
    page = title.split("|", 1)[0].strip().replace(" ", "_")
    return page or None


def wiki_url(page):
    return WIKI + quote(page, safe="/:_-'()")


async def existing_urls(pages):
    if not pages:
        return []

    params = {
        "action": "query",
        "format": "json",
        "titles": "|".join(page.replace("_", " ") for page in pages),
    }
    try:
        async with bot.wiki_session.get(API, params=params) as response:
            data = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as error:
        print(f"Wiki check failed: {error}")
        return [wiki_url(page) for page in pages]

    if "query" not in data:
        print(f"Wiki check failed: {data.get('error', data)}")
        return [wiki_url(page) for page in pages]

    found = set()
    for info in data["query"].get("pages", {}).values():
        if "missing" in info or "invalid" in info:
            continue
        title = info.get("title")
        if title:
            found.add(title.replace("_", " ").casefold())

    return [
        wiki_url(page)
        for page in pages
        if page.replace("_", " ").casefold() in found
    ]


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
    session = getattr(bot, "wiki_session", None)
    if session is None or session.closed:
        bot.wiki_session = aiohttp.ClientSession(
            headers={"User-Agent": "ScroompendiumBot/1.0"},
            timeout=aiohttp.ClientTimeout(total=10),
        )
    print(f"Connected as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot or not is_allowed(message):
        return

    pages = []
    for title in WIKILINK.findall(message.content):
        page = page_name(title)
        if page and page not in pages:
            pages.append(page)
        if len(pages) == 3:
            break

    urls = await existing_urls(pages)
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