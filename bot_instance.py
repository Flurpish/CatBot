import discord
from discord.ext import commands

# Define intents here or import them from config if you prefer
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix=None, intents=intents)
