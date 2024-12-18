import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = 1286455113589850112
LOG_CHANNEL_ID = 1286481588179308604
DATABASE_PATH = 'practice_logger.db'
