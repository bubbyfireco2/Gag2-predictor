import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import random
import asyncio
import time
from flask import Flask
from threading import Thread

# --- MINIMAL FLASK SERVER TO TRICK RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Predictor Clean-Channel Matrix is online!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- CONFIGURATION SETTINGS ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  
CHANNEL_ID = 1518727458919284937  

# Pasting the channel IDs from both source servers here
SEED_CHANNEL_ID = 123456789012345678  
GEAR_CHANNEL_ID = 876543210987654321  

DATA_FILE = "/opt/render/project/src/probability_memory.json" if os.environ.get("RENDER") else "probability_memory.json"

ALL_ITEMS_ODDS = {
    "Carrot": 100.0, "Strawberry": 100.0, "Blueberry": 100.0, "Tulip": 100.0, "Tomato": 90.0, "Apple": 52.0, 
    "Bamboo": 80.0, "Corn": 25.0, "Cactus": 16.6, "Pineapple": 12.5, "Mushroom": 9.0, "Green Bean": 15.0, 
    "Banana": 9.0, "Grape": 6.6, "Coconut": 5.0, "Mango": 5.0, "Dragon Fruit": 4.0, "Acorn": 2.9, 
    "Cherry": 2.2, "Sunflower": 1.7, "Venus Fly Trap": 1.43, "Pomegranate": 0.9, "Poison Apple": 0.5, 
    "Venom Splitter": 0.475, "Moon Bloom": 0.35, "Dragon's Breath": 0.275,
    "Common Sprinkler": 50.0, "Uncommon Sprinkler": 35.0, "Rare Sprinkler": 25.0, "Legendary Sprinkler": 4.0, 
    "Super Sprinkler": 1.2, "Common Watering Can": 90.0, "Super Watering Can": 2.0, "Trowel": 28.0, 
    "Jump Mushroom": 24.0, "Speed Mushroom": 22.0, "Supersize Mushroom": 10.0, "Invisibility Mushroom": 4.0, 
    "Shrink Mushroom": 10.0, "Gnome": 8.0, "Basic Pot": 7.0, "Flashbang": 7.0
}

WEATHER_EVENTS = ["Normal Clear Night", "Gold Moon Midas Event 🌟", "Lightning Storm ⚡", "Rainbow Aurora 🌈", "Blood Moon 🌙"]

memory = {"last_seen": {}, "current_stock": []}

sent_hourly_pings = {}
sent_five_min_pings = {}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f: memory = json.load(f)
    except: pass

if "enabled_alerts" not in memory:
    memory["enabled_alerts"] = {}

def save_data():
    with open(DATA_FILE, "w") as f: json.dump(memory, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    print('Squeezed Mobile Layout Predictor is running!')
    dashboard_refresh_loop.start()

# --- DYNAMIC ALERT MANAGEMENT COMMAND MODULES ---
@bot.command(name="alert")
async def toggle_item_alert(ctx, *, item_and_mode: str):
    raw_input = item_and_mode.strip()
    parts = raw_input.rsplit(" ", 1)
    if len(parts) < 2 or parts[1].lower() not in ["on", "off"]:
        await ctx.send("❌ **Invalid Format!** Use: `!alert (item name) on` or `!alert (item name) off`")
        return
        
    target_item_raw = parts[0].strip()
    mode = parts[1].lower()
    
    matched_item = None
    for official_name in ALL_ITEMS_ODDS.keys():
        if official_name.lower() == target_item_raw.lower():
            matched_item = official_name
            break
            
    if not matched_item:
        await ctx.send(f"❌ **Item Not Found!** Spell check name tracker parameter `{target_item_raw}`.")
        return
        
    if mode == "on":
        memory["enabled_alerts"][matched_item] = True
        save_data()
        await ctx.send(f"BC-🔔 **Alert Enabled!** I will ping @everyone for **{matched_item}** changes.")
    else:
        if matched_item in memory["enabled_alerts"]:
            del memory["enabled_alerts"][matched_item]
        save_data()
        await ctx.send(f"BC-🔕 **Alert Disabled!** Turned off pings for **{matched_item}**.")

@bot.command(name="alerts")
async def list_alert_status(ctx):
    enabled_list = [f"• {item}" for item in ALL_ITEMS_ODDS.keys() if memory["enabled_alerts"].get(item)]
    embed = discord.Embed(title="🔔 Active Notification Settings Status", color=discord.Color.blue())
    if enabled_list:
        embed.description = "**Currently Active Alerts:**\n" + "\n".join(enabled_list)
    else:
        embed.description = "All alerts are currently **disabled** by default.\nUse `!alert (item) on` to turn one on!"
    await ctx.send(embed=embed)

# --- HIGH-DENSITY SQUEEZED MOBILE TABLE GENERATOR ---
async def generate_compact_dashboard(channel):
    now = datetime.datetime.now(datetime.timezone.utc)
    now_ts = int(time.time())
    
    next_global_rotation_ts = ((now_ts // 300) + 1) * 300
    secs_remaining = next_global_rotation_ts - now_ts
    mins_remaining_live = secs_remaining // 60
    secs_remaining_live = secs_remaining % 60
    
    in_stock_list = memory.get("current_stock", [])
    
    stock_text = "🟢 **CURRENT SHOP INVENTORY:**\n```text\n"
    if in_stock_list:
        stock_text += " | ".join(in_stock_list) + "\n"
    else:
        stock_text += "Waiting for active log signals from server channels...\n"
    stock_text += f"```\n⏱️ **NEXT GLOBAL SHOP RESTOCK IN:** `{mins_remaining_live:02d}m {secs_remaining_live:02d}s`\n\n"

    seeds_table = "```diff\n=== SEEDS RESTOCK ESTIMATES ===\n"
    gear_table = "```diff\n=== GEARS RESTOCK ESTIMATES ===\n"
    
    seed_keys = ["Carrot", "Strawberry", "Blueberry", "Tulip", "Tomato", "Apple", "Bamboo", "Corn", "Cactus", "Pineapple", "Mushroom", "Green Bean", "Banana", "Grape", "Coconut", "Mango", "Dragon Fruit", "Acorn", "Cherry", "Sunflower", "Venus Fly Trap", "Pomegranate", "Poison Apple", "Venom Splitter", "Moon Bloom", "Dragon's Breath"]
    
    upcoming_alerts_display = []

    for item, base_chance in ALL_ITEMS_ODDS.items():
        is_alert_enabled = memory["enabled_alerts"].get(item, False)
        
        if item in in_stock_list:
            time_str = "NOW"
            chance_str = "100%"
            prefix = "+ "
        elif item in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][item])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            expected_interval_minutes = round((100 / base_chance) * 5)
            minutes_remaining = max(5, expected_interval_minutes - minutes_since)
            
            chance_of_missing = 1 - (base_chance / 100)
            accumulated_odds = (1 - (chance_of_missing ** max(1, rotations_missed))) * 100
            
            time_str = f"{minutes_remaining}m"
            chance_str = f"{accumulated_odds:.1f}%"
            prefix = "- " if accumulated_odds > 75 else "  "
            
            if is_alert_enabled:
                if minutes_remaining <= 5:
                    upcoming_alerts_display.append(f"🚨 **{item} ARRIVING NEXT BLOCK (~5m)!**")
                    if item not in sent_five_min_pings or (now_ts - sent_five_min_pings[item] > 600):
                        sent_five_min_pings[item] = now_ts
                        bot.loop.create_task(channel.send(f"⚠️ @everyone **URGENT RESTOCK ALERT:** **{item}** is predicted to return in the **VERY NEXT ROTATION** (under 5 minutes left)! Get ready!"))
                        
                elif minutes_remaining <= 60:
                    upcoming_alerts_display.append(f"⚠️ **{item}** expected back in ~**{minutes_remaining}m**!")
                    if item not in sent_hourly_pings or (now_ts - sent_hourly_pings[item] > 3600):
                        sent_hourly_pings[item] = now_ts
                        bot.loop.create_task(channel.send(f"📡 @everyone **1-Hour Restock Tracker Notice:** **{item}** is estimated to drop within the next hour (~{minutes_remaining} minutes remaining)."))
        else:
            time_str = f"{round((100/base_chance)*5)}m"
            chance_str = f"{base_chance}%"
            prefix = "  "

        row = f"{prefix}{item:<14} | Nxt:{time_str:<5} | Odds:{chance_str}\n"
        
        if item in seed_keys:
            seeds_table += row
        else:
            gear_table += row

    seeds_table += "```"
    gear_table += "```\n"
    
    hour_seed = now_ts // 3600
    random.seed(hour_seed)
    predicted_weather = random.choice(WEATHER_EVENTS)
    minutes_until_hour_flip = 60 - (int(time.time()) // 60 % 60)
    
    gear_table += f"🌙 **NIGHT WEATHER FORECAST:**\n```🔮 Current Block: {predicted_weather}```\n⏳ *Next Weather Event Shakes up in:* **{minutes_until_hour_flip} minutes**\n\n"
    
    if upcoming_alerts_display:
        gear_table += "🚨 **CRITICAL USER-SELECTED ALERTS:**\n" + "\n".join(upcoming_alerts_display)

    await channel.send(stock_text)
    await channel.send(seeds_table)
    await channel.send(gear_table)

# --- HIGH-FREQUENCY LIVE REFRESH LOOP ---
@tasks.loop(seconds=10)
async def dashboard_refresh_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    # 🔥 THE CHANNELS CLEANER ENGINE: Purges all historical text layout blocks cleanly
    try:
        await channel.purge(limit=100)
    except Exception as e:
        print(f"Purge Warning (Ensure bot has 'Manage Messages' permission): {e}")
    
    await generate_compact_dashboard(channel)

# --- MASTER EMBED PARSER INTERCEPTOR ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id in [SEED_CHANNEL_ID, GEAR_CHANNEL_ID]:
        text_dump = []
        if message.content: text_dump.append(message.content)
        if message.embeds:
            for embed in message.embeds:
                if embed.title: text_dump.append(embed.title)
                if embed.description: text_dump.append(embed.description)
                if embed.fields:
                    for field in embed.fields:
                        text_dump.append(field.name)
                        text_dump.append(field.value)

