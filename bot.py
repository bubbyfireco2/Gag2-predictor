import os
import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import asyncio

# Create Flask web hook server
app = Flask(__name__)

# Load secret variables from Render's dashboard environment
TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@app.route('/')
def home():
    return "Bot is alive and listening!", 200

@app.route('/weather-update', methods=['POST'])
def weather_update():
    data = request.json
    event_name = data.get("eventName", "Clear Skies")
    offset_seconds = data.get("offsetSeconds", 0)
    
    # Push data to Discord thread
    asyncio.run_coroutine_threadsafe(
        send_prediction_alert(event_name, offset_seconds), 
        bot.loop
    )
    return jsonify({"status": "received"}), 200

async def send_prediction_alert(event, seconds):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        minutes = int(seconds // 60)
        remaining_secs = int(seconds % 60)
        
        embed = discord.Embed(
            title="☀️ GAAG 2 MID-DAY PREDICTION", 
            color=discord.Color.blue()
        )
        embed.add_field(name="Upcoming Event", value=f"**{event}**", inline=False)
        embed.add_field(
            name="Starts In", 
            value=f"⏳ **{minutes}m {remaining_secs}s** from Dawn mark", 
            inline=False
        )
        embed.set_footer(text="Global Sync Cloud Tracker")
        await channel.send(embed=embed)

def run_discord():
    bot.run(TOKEN)

# Run Discord on its own thread so Flask can keep the Render server active
threading.Thread(target=run_discord, daemon=True).start()

