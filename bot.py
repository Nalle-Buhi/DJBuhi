import os
import discord
import sqlite3
from discord.ext import commands
from creds import TOKEN

class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    em = discord.Embed(title="Help", description="Djbuhi on siirtynyt slash komentoihin, kaikki komennot näet kirjoittamalla '/' chattiin", color=discord.Color.green())

    async def send_bot_help(self, mapping):
        await self.get_destination().send(embed=self.em)



bot = commands.Bot(command_prefix=["bdj ", "Bdj "], case_insensitive=True, help_command=Help())

# load cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print(f"loaded: {filename}")

@bot.event
async def on_ready():

    print(f"Logged in {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("bdj help"))


bot.run(TOKEN)