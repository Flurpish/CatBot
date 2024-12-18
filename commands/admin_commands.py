import discord
from discord import app_commands
import pytz
import aiosqlite
from bot_instance import bot
from utils import is_admin, is_admin_plus, add_to_file, remove_from_file, read_file
from database import add_hours_to_db
from datetime import datetime, timedelta
from config import LOG_CHANNEL_ID, GUILD_ID  # Make sure GUILD_ID is imported
# These commands require admin or admin+ privileges

@bot.tree.command(
    name="adminlist", 
    description="List all bot and admins.", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(visible="Make the output visible to everyone? Defaults to False.")
async def adminlist(interaction: discord.Interaction, visible: bool = False):
    admin_plus = read_file("admin_plus.txt")
    admins = read_file("admins.txt")

    embed = discord.Embed(
        title="Admin List",
        description="List of Admin+ and admins.",
        color=discord.Color.blue(),
    )

    if admin_plus:
        admin_plus_list = "\n".join([f"{username} (ID: {user_id})" for user_id, username in admin_plus.items()])
        embed.add_field(name="Admin+", value=admin_plus_list, inline=False)
    else:
        embed.add_field(name="Admin+", value="No Admin+ found.", inline=False)

    if admins:
        admins_list = "\n".join([f"{username} (ID: {user_id})" for user_id, username in admins.items()])
        embed.add_field(name="Admins", value=admins_list, inline=False)
    else:
        embed.add_field(name="Admins", value="No admins found.", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=not visible)


@bot.tree.command(
    name="addadmin", 
    description="Add an admin to the bot (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="The user to be added as an admin.")
async def addadmin(interaction: discord.Interaction, user: discord.User):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    add_to_file("admins.txt", user.id, user.name)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"{interaction.user.display_name} added {user.display_name} as an admin.")
    await interaction.response.send_message(f"{user.display_name} has been added as an admin.", ephemeral=True)


@bot.tree.command(
    name="removeadmin", 
    description="Remove an admin from the bot (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="The user to remove from admin list.")
async def removeadmin(interaction: discord.Interaction, user: discord.User):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    if user.id == interaction.user.id:
        await interaction.response.send_message("You can't remove yourself!", ephemeral=True)
        return

    remove_from_file("admins.txt", user.id)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"{interaction.user.display_name} removed {user.display_name} from admin roles.")
    await interaction.response.send_message(f"{user.display_name} has been removed as an admin.", ephemeral=True)


@bot.tree.command(
    name="addadminplus", 
    description="Add a bot admin (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="The user to be added as a bot admin.")
async def addadminplus(interaction: discord.Interaction, user: discord.User):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    add_to_file("admin_plus.txt", user.id, user.name)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"{interaction.user.display_name} added {user.display_name} as a bot admin.")
    await interaction.response.send_message(f"{user.display_name} added as a bot admin.", ephemeral=True)


@bot.tree.command(
    name="removeadminplus", 
    description="Remove a bot admin (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="The user to remove from bot admin list.")
async def removeadminplus(interaction: discord.Interaction, user: discord.User):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    if user.id == interaction.user.id:
        await interaction.response.send_message("You can't remove yourself!", ephemeral=True)
        return

    remove_from_file("admin_plus.txt", user.id)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"{interaction.user.display_name} removed {user.display_name} from bot admin roles.")
    await interaction.response.send_message(f"{user.display_name} has been removed as a bot admin.", ephemeral=True)


@bot.tree.command(
    name="resetweek", 
    description="Reset all logged hours for the week (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
async def resetweek(interaction: discord.Interaction):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    try:
        async with aiosqlite.connect('practice_logger.db') as db:
            await db.execute("DELETE FROM hours")
            await db.commit()

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"{interaction.user.display_name} reset all logged hours for the week.")

        await interaction.response.send_message("All logged hours have been reset.", ephemeral=True)
    except Exception as e:
        print(f"Error in resetweek: {e}")
        await interaction.response.send_message("Error resetting the week.", ephemeral=True)


@bot.tree.command(
    name="reset", 
    description="Reset hours for a user for a specific day or full week (Admin only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    day="The day to reset (optional). If not provided, resets the full week.",
    user="The user whose hours are to be reset."
)
async def reset(interaction: discord.Interaction, user: discord.User, day: str = None):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    admin_name = interaction.user.display_name
    try:
        async with aiosqlite.connect('practice_logger.db') as db:
            today = datetime.now(pytz.timezone("America/Chicago"))
            start_of_week = today - timedelta(days=today.weekday())

            if day:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                if day.capitalize() not in days:
                    await interaction.response.send_message("Invalid day.", ephemeral=True)
                    return

                day_index = days.index(day.capitalize())
                target_date = start_of_week + timedelta(days=day_index)
                target_date_str = target_date.strftime('%Y-%m-%d')
                await db.execute("DELETE FROM hours WHERE user_id = ? AND date = ?", (user.id, target_date_str))
                await db.commit()
                await interaction.response.send_message(f"Reset hours for {user.display_name} on {day}.", ephemeral=True)
                log_message = f"{admin_name} reset hours for {user.display_name} on {day}."
            else:
                start_of_week_str = start_of_week.strftime('%Y-%m-%d')
                await db.execute("DELETE FROM hours WHERE user_id = ? AND date >= ?", (user.id, start_of_week_str))
                await db.commit()
                await interaction.response.send_message(f"Reset hours for {user.display_name} for the full week.", ephemeral=True)
                log_message = f"{admin_name} reset hours for {user.display_name} for the full week."

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(log_message)

    except Exception as e:
        print(f"Error in /reset command: {e}")
        await interaction.response.send_message("Error resetting hours.", ephemeral=True)


@bot.tree.command(
    name="add", 
    description="Add hours to a specific game for a user on a specific day (Admin only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    day="Day of the week (e.g. Monday)",
    game="The game name",
    hours="Number of hours",
    user="User to add hours for"
)
async def add_hours(interaction: discord.Interaction, day: str, game: str, hours: float, user: discord.User):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day.capitalize() not in days:
        await interaction.response.send_message("Invalid day.", ephemeral=True)
        return

    admin_name = interaction.user.display_name
    try:
        cst = pytz.timezone("America/Chicago")
        today = datetime.now(cst)
        start_of_week = today - timedelta(days=today.weekday())
        day_index = days.index(day.capitalize())
        target_date = start_of_week + timedelta(days=day_index)
        target_date_str = target_date.strftime('%Y-%m-%d')

        await add_hours_to_db(user.id, game, target_date_str, hours, f"Added by {admin_name}")
        await interaction.response.send_message(f"Added {hours} hours for {user.display_name} on {game} for {day}.", ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"{admin_name} added {hours} hours to {user.display_name} for {game} on {day}.")
    except Exception as e:
        print(f"Error in /add: {e}")
        await interaction.response.send_message("Error adding hours.", ephemeral=True)


@bot.tree.command(
    name="remove", 
    description="Remove hours from a specific game for a user on a specific day (Admin only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    day="Day of the week",
    game="The game name",
    hours="Number of hours to remove",
    user="User to remove hours from"
)
async def remove_hours(interaction: discord.Interaction, day: str, game: str, hours: float, user: discord.User):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day.capitalize() not in days:
        await interaction.response.send_message("Invalid day.", ephemeral=True)
        return

    admin_name = interaction.user.display_name
    cst = pytz.timezone("America/Chicago")
    today = datetime.now(cst)
    start_of_week = today - timedelta(days=today.weekday())
    day_index = days.index(day.capitalize())
    target_date = start_of_week + timedelta(days=day_index)
    target_date_str = target_date.strftime('%Y-%m-%d')

    try:
        async with aiosqlite.connect('practice_logger.db') as db:
            query = '''SELECT hours FROM hours WHERE user_id = ? AND date = ? AND game = ?'''
            async with db.execute(query, (user.id, target_date_str, game)) as cursor:
                row = await cursor.fetchone()

            if not row:
                await interaction.response.send_message(f"No hours found for {game} on {day} for {user.display_name}.", ephemeral=True)
                return

            existing_hours = row[0]
            if existing_hours < hours:
                await interaction.response.send_message("Not enough hours to remove.", ephemeral=True)
                return

            new_hours = existing_hours - hours
            if new_hours == 0:
                await db.execute("DELETE FROM hours WHERE user_id = ? AND date = ? AND game = ?", (user.id, target_date_str, game))
            else:
                await db.execute("UPDATE hours SET hours = ? WHERE user_id = ? AND date = ? AND game = ?", (new_hours, user.id, target_date_str, game))
            await db.commit()

        await interaction.response.send_message(f"Removed {hours} hours for {user.display_name} on {game} for {day}.", ephemeral=True)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"{admin_name} removed {hours} hours from {user.display_name} for {game} on {day}.")
    except Exception as e:
        print(f"Error in /remove command: {e}")
        await interaction.response.send_message("Error removing hours.", ephemeral=True)


@bot.tree.command(
    name="setdailyinfo", 
    description="Set channel/message ID for daily button management (Admin+ only).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(channel_id="Channel ID", message_id="Message ID")
async def set_daily_info(interaction: discord.Interaction, channel_id: str, message_id: str):
    from daily import daily_info
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    try:
        daily_info["channel_id"] = int(channel_id)
        daily_info["message_id"] = int(message_id)
        await interaction.response.send_message(
            f"Daily setup updated. Channel ID: `{channel_id}`, Message ID: `{message_id}`", ephemeral=True
        )
    except ValueError:
        await interaction.response.send_message("Invalid IDs, must be integers.", ephemeral=True)


@bot.tree.command(
    name="clearbuttons", 
    description="Remove all buttons from a message (Admin+).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(message_id="Message ID to clear buttons from.")
async def clear_buttons_cmd(interaction: discord.Interaction, message_id: str):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    try:
        channel = interaction.channel
        message = await channel.fetch_message(int(message_id))
        await message.edit(view=None)
        await interaction.response.send_message(f"Removed all buttons from message {message_id}", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("Message not found.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("No permission to edit this message.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Error clearing buttons: {e}", ephemeral=True)


@bot.tree.command(
    name="adddaily", 
    description="Manually trigger daily logic with a specific day (Admin+).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(day="e.g., Monday, Tuesday...")
async def adddaily(interaction: discord.Interaction, day: str):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day not in valid_days:
        await interaction.response.send_message(f"Invalid day. Choose from: {', '.join(valid_days)}", ephemeral=True)
        return

    from daily import dailyButtons
    await dailyButtons(test_day=day)
    await interaction.response.send_message(f"Daily buttons logic executed for {day}.", ephemeral=True)


@bot.tree.command(
    name="addbuttons", 
    description="Add buttons to a message for all days (Admin+).", 
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(message_id="The message ID to add buttons to.")
async def add_buttons(interaction: discord.Interaction, message_id: str):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message('Not authorized.', ephemeral=True)
        return

    from views import DayButtonView
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    view = DayButtonView(days)
    try:
        message = await interaction.channel.fetch_message(message_id)
        await message.edit(view=view)
        await interaction.response.send_message(f'Added buttons to message {message_id}.', ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message('Message not found.', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message('No permission.', ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Error adding buttons: {e}", ephemeral=True)
