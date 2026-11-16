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

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def wiki_url(title):
    page = title.split("|", 1)[0].strip().replace(" ", "_")
    if not page:
        return None
    return WIKI + quote(page, safe="/:_-'()")


@bot.event
async def on_ready():
    print(f"Connected as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    urls = []
    for title in WIKILINK.findall(message.content):
        url = wiki_url(title)
        if url and url not in urls:
            urls.append(url)

    if urls:
        await message.channel.send("\n".join(urls))

    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.display_name}")


@bot.command()
async def echo(ctx, *, text: str):
    await ctx.send(text)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Add some text after the command. Example: !echo hello")
        return
    raise error


bot.run(token)