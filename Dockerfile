FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Flask (server.py)
EXPOSE 8080

# Start the bot
CMD ["python", "bot.py"]
