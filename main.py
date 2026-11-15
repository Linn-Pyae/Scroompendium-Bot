import os

import discord
from discord.ext import commands

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is required")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Connected as {bot.user}")


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