import discord
import logging
from discord.ext import commands
from config import TOKEN, GUILD_ID, LOG_CHANNEL_ID
from database import init_db, migrate_db_schema
from utils import is_admin_plus
from bot_instance import bot
from views import DayButtonView
from daily import schedule_daily_buttons

logging.basicConfig(level=logging.INFO)

# Import commands after bot is defined
from commands.admin_commands import *
from commands.user_commands import *
from commands.embed_commands import *
from commands.report_commands import *

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    try:
        # Sync guild-specific commands
        guild = discord.Object(id=GUILD_ID)
        guild_commands = await bot.tree.sync(guild=guild)
        print(f"Synced {len(guild_commands)} guild commands for GUILD_ID {GUILD_ID}.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    bot.add_view(DayButtonView([]))
    bot.loop.create_task(schedule_daily_buttons())

    print(f'{bot.user} has connected to Discord!')
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send("I'm awake!")

    



bot.run(TOKEN)
