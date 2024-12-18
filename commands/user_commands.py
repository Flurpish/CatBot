import discord
from discord import app_commands
import pytz
from datetime import datetime, timedelta
import aiosqlite
from config import LOG_CHANNEL_ID
from utils import is_admin, get_allowed_games
from bot_instance import bot
from config import GUILD_ID

@bot.tree.command(name='ping', description='Check the bot\'s latency.',  guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')


@bot.tree.command(name="hours", description="View your logged hours for the week.",  guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="Optional: specify another user (Admin only)",
    visible="Make output visible to everyone?"
)
async def hours(interaction: discord.Interaction, user: discord.User = None, visible: bool = False):
    target_user = user or interaction.user
    await interaction.response.defer(ephemeral=not visible)

    if user and user != interaction.user and not is_admin(interaction.user.id):
        await interaction.followup.send("You aren't authorized to view someone else's hours.", ephemeral=True)
        return

    try:
        async with aiosqlite.connect('practice_logger.db') as db:
            today = datetime.now(pytz.timezone("America/Chicago"))
            start_of_week = today - timedelta(days=today.weekday())
            start_of_week_str = start_of_week.strftime('%Y-%m-%d')

            query = '''
                SELECT date, game, SUM(hours) as total_hours, details
                FROM hours
                WHERE user_id = ? AND date >= ?
                GROUP BY date, game, details
                ORDER BY date, game
            '''
            async with db.execute(query, (target_user.id, start_of_week_str)) as cursor:
                logs = await cursor.fetchall()

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            logs_by_day = {day: [] for day in days}
            weekly_totals = {}

            for log_date, game, hrs, details in logs:
                log_date_obj = datetime.strptime(log_date, '%Y-%m-%d')
                day_name = log_date_obj.strftime('%A')
                logs_by_day[day_name].append(f"{game}: {hrs:.2f} hours - {details}")
                weekly_totals[game] = weekly_totals.get(game, 0) + hrs

            embed = discord.Embed(
                title=f"Weekly Logged Hours for {target_user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            for day, entries in logs_by_day.items():
                if entries:
                    embed.add_field(name=day, value="\n".join(entries), inline=False)
                else:
                    embed.add_field(name=day, value="No hours logged", inline=False)

            totals_str = "\n".join([f"{g}: {t:.2f} hours" for g, t in weekly_totals.items()]) or "No hours logged."
            embed.add_field(name="Weekly Totals by Game", value=totals_str, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=not visible)
    except Exception as e:
        print(f"Error in /hours: {e}")
        await interaction.followup.send("Error retrieving hours.", ephemeral=True)


@bot.tree.command(name="games", description="Show the list of allowed games.",  guild=discord.Object(id=GUILD_ID))
@app_commands.describe(visible="Make output visible?")
async def games(interaction: discord.Interaction, visible: bool = False):
    allowed_games = get_allowed_games()
    if not allowed_games:
        await interaction.response.send_message("No allowed games defined.", ephemeral=not visible)
        return

    embed = discord.Embed(
        title="Allowed Games",
        description="\n".join([f"- {g}" for g in allowed_games]),
        color=discord.Color.blue()
    )
    embed.set_footer(text="Use these exact names to log your hours.")
    await interaction.response.send_message(embed=embed, ephemeral=not visible)