import discord
import pytz
from datetime import datetime, timedelta
from discord.ui import Modal, TextInput
from utils import get_allowed_games
from database import add_hours_to_db
from config import LOG_CHANNEL_ID
from bot_instance import bot  # Import bot from bot_instance, not from main

class LogHoursModal(discord.ui.Modal):
    """A modal to log game hours."""

    def __init__(self, day: str):
        super().__init__(title=f"Log Hours for {day}")
        self.day = day

        # Game Name (Required)
        self.game_name = discord.ui.TextInput(
            label="Game Name",
            placeholder="Enter the game's name (e.g., League of Legends)",
            required=True,
            max_length=100,
        )
        self.add_item(self.game_name)

        # Hours Played Today (Required)
        self.hours_played = discord.ui.TextInput(
            label="Hours Played Today",
            placeholder="Enter the number of hours (e.g., 2.5)",
            required=True,
            max_length=10,
        )
        self.add_item(self.hours_played)

        # Additional Information (Optional)
        self.additional_info = discord.ui.TextInput(
            label="Additional Information",
            placeholder="Any extra details (optional)",
            required=False,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.additional_info)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission and save data to the database."""
        game_name = self.game_name.value.strip()
        hours_input = self.hours_played.value.strip()
        additional_info = self.additional_info.value.strip() or "No additional information provided."

        # Validate game name
        allowed_games = get_allowed_games()
        if game_name not in allowed_games:
            await interaction.response.send_message(
                f"Invalid game name. Allowed games are: {', '.join(allowed_games)}.",
                ephemeral=True,
            )
            return

        # Validate hours as float
        try:
            hours = float(hours_input)
            if hours <= 0:
                raise ValueError("Hours must be positive.")
        except ValueError:
            await interaction.response.send_message(
                "Invalid input for hours. Enter a positive number (e.g., 2.5).",
                ephemeral=True,
            )
            return

        try:
            today = datetime.now(pytz.timezone("America/Chicago"))
            start_of_week = today - timedelta(days=today.weekday())
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_index = days.index(self.day)
            target_date = start_of_week + timedelta(days=day_index)
            target_date_str = target_date.strftime('%Y-%m-%d')

            # Use the helper function to add hours
            await add_hours_to_db(interaction.user.id, game_name, target_date_str, hours, additional_info)

            # Log to the channel
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"{interaction.user.display_name} has added {hours} hours for {game_name} on {self.day}."
                )

            # Notify the user
            await interaction.response.send_message(
                f"**Logged Hours for {self.day}:**\n"
                f"- **Game Name:** {game_name}\n"
                f"- **Hours Played Today:** {hours}\n"
                f"- **Additional Information:** {additional_info}\n\n"
                f"The data has been saved successfully!",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error saving data to database: {e}")
            await interaction.response.send_message(
                "An error occurred while saving your data. Please try again later.",
                ephemeral=True,
            )


            # Get the target date
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            today = datetime.now(pytz.timezone("America/Chicago"))
            start_of_week = today - timedelta(days=today.weekday())
            day_index = days.index(self.day)
            target_date = start_of_week + timedelta(days=day_index)
            target_date_str = target_date.strftime('%Y-%m-%d')

            # Consolidate hours
            await add_hours_to_db(interaction.user.id, game_name, target_date_str, hours, additional_info)

            await interaction.response.send_message(
                f"Logged {hours} hours for {game_name} on {self.day}.\nAdditional Info: {additional_info}",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("Invalid input for hours. Please enter a positive number.", ephemeral=True)
        except Exception as e:
            print(f"Error in LogHoursModal: {e}")
            await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)
    
# Add Weekly Buttons
class DayButtonView(discord.ui.View):
    """A view containing buttons for each day of the week."""
    def __init__(self, days):
        super().__init__(timeout=None)
        for day in days:
            button = discord.ui.Button(label=day, style=discord.ButtonStyle.primary, custom_id=f"day_{day.lower()}")
            button.callback = self.button_callback  # Attach the callback dynamically
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        """Callback for button interactions."""
        # Extract custom_id from interaction data
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("day_"):
            day = custom_id.split('_')[1].capitalize()
            
            # Trigger the modal
            modal = LogHoursModal(day)
            await interaction.response.send_modal(modal)
