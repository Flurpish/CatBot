import discord
from discord import app_commands
from utils import is_admin_plus
from bot_instance import bot
import os
from config import GUILD_ID

@bot.tree.command(name="sendembed", description="Send an embedded message to a specified channel (Admin+).", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    channel_id="Channel ID (optional, defaults to current)",
    title="Embed title",
    description="Embed description"
)
async def sendembed(interaction: discord.Interaction, title: str, description: str, channel_id: str = None):
    if not is_admin_plus(interaction.user.id):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return

    try:
        target_channel = bot.get_channel(int(channel_id)) if channel_id else interaction.channel
        if not target_channel:
            await interaction.response.send_message("Invalid channel.", ephemeral=True)
            return

        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        await target_channel.send(embed=embed)
        await interaction.response.send_message(f"Embed sent to {target_channel.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="commands", description="List all commands with categories.", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(visible="Make output visible to everyone?")
async def commands_list(interaction: discord.Interaction, visible: bool = False):
    if not os.path.exists("commands.txt"):
        await interaction.response.send_message("Commands file missing.", ephemeral=True)
        return

    try:
        with open("commands.txt", "r") as file:
            lines = [l.strip() for l in file if l.strip()]

        admin_plus_cmds = []
        admin_cmds = []
        normal_cmds = []
        current_category = None

        for line in lines:
            lower = line.lower()
            if lower == "[admin+]":
                current_category = admin_plus_cmds
            elif lower == "[admin]":
                current_category = admin_cmds
            elif lower == "[normal]":
                current_category = normal_cmds
            else:
                if current_category is not None:
                    current_category.append(line)

        embed = discord.Embed(
            title="Available Commands",
            description="Commands categorized by roles.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Admin+ Commands", value="\n".join(admin_plus_cmds) if admin_plus_cmds else "None", inline=False)
        embed.add_field(name="Admin Commands", value="\n".join(admin_cmds) if admin_cmds else "None", inline=False)
        embed.add_field(name="Normal Commands", value="\n".join(normal_cmds) if normal_cmds else "None", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=not visible)
    except Exception as e:
        print(f"Error in /commands: {e}")
        await interaction.response.send_message("Error reading commands file.", ephemeral=True)
