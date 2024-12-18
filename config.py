import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = 717936676886020166
LOG_CHANNEL_ID = 803387116989055006
DATABASE_PATH = 'practice_logger.db'
