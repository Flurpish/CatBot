import discord
from discord import app_commands
from utils import is_admin, generate_report_file
from bot_instance import bot
from config import GUILD_ID

@bot.tree.command(name="report", description="Generate an Excel report of all logged hours (Admin).",  guild=discord.Object(id=GUILD_ID))
@app_commands.describe(visible="Make the report visible?")
async def report(interaction: discord.Interaction, visible: bool = False):
    await interaction.response.defer(ephemeral=not visible)

    if not is_admin(interaction.user.id):
        await interaction.followup.send("You are not authorized to generate reports.", ephemeral=True)
        return

    try:
        file_path = await generate_report_file(interaction.guild)
        await interaction.followup.send(
            content="Here is the compiled report:",
            file=discord.File(file_path),
            ephemeral=not visible
        )
    except Exception as e:
        print(f"Error in /report command: {e}")
        await interaction.followup.send(
            content="An error occurred while generating the report. Please try again later.",
            ephemeral=True
        )
