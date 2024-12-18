import asyncio
import pytz
from datetime import datetime, timedelta
import discord
from views import DayButtonView
from bot_instance import bot
from config import LOG_CHANNEL_ID

daily_info = {"channel_id": None, "message_id": None}

async def schedule_daily_buttons():
    while True:
        cst = pytz.timezone("America/Chicago")
        now = datetime.now(cst)
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_duration = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_duration)
        await dailyButtons()

async def dailyButtons(test_day=None):
    if not daily_info["channel_id"] or not daily_info["message_id"]:
        print("Daily info not set. Use /setdailyinfo command.")
        return

    cst = pytz.timezone("America/Chicago")
    today = test_day or datetime.now(cst).strftime("%A")

    channel = bot.get_channel(daily_info["channel_id"])
    if not channel:
        print("Channel not found.")
        return

    match today:
        case "Monday":
            await clearbuttons(daily_info["message_id"], channel)
            await addbuttons(daily_info["message_id"], channel, "Monday")
        case other:
            await addbuttons(daily_info["message_id"], channel, today)

async def addbuttons(message_id, channel, new_day):
    try:
        message = await channel.fetch_message(int(message_id))
        if message.components:
            existing_days = [
                component.label
                for row in message.components
                for component in row.children
            ]
        else:
            existing_days = []
        if new_day not in existing_days:
            existing_days.append(new_day)
        view = DayButtonView(existing_days)
        await message.edit(view=view)
    except Exception as e:
        print(f"Error in addbuttons: {e}")

async def clearbuttons(message_id, channel):
    try:
        message = await channel.fetch_message(int(message_id))
        await message.edit(view=None)
    except Exception as e:
        print(f"Error in clearbuttons: {e}")
