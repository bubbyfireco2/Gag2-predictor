import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import random
import asyncio
import urllib.request
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- MINIMAL FLASK SERVER TO TRICK RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Predictor Web-Scraper Engine is online!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- CONFIGURATION SETTINGS ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  
CHANNEL_ID = 1518727458919284937  # Your personal alert channel ID where predictions post

DATA_FILE = "/opt/render/project/src/probability_memory.json" if os.environ.get("RENDER") else "probability_memory.json"

# COMBINED ACCURATE PERCENTAGE DATABASE
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

memory = {"last_seen": {}, "current_stock": []}
active_messages = []

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f: memory = json.load(f)
    except: pass

def save_data():
    with open(DATA_FILE, "w") as f: json.dump(memory, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    print('Targeted Card-Scraper is online!')
    sixty_second_clock_loop.start()

# --- HIGH-DENSITY SHRUNK TEXT TABLE GENERATOR ---
async def generate_compact_dashboard(channel):
    global active_messages
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. CURRENTLY IN STOCK HEADER
    in_stock_list = memory.get("current_stock", [])
    stock_text = "🟢 **CURRENT SHOP INVENTORY:**\n```text\n"
    if in_stock_list:
        stock_text += " | ".join(in_stock_list) + "\n"
    else:
        stock_text += "Fetching active inventory from game servers...\n"
    stock_text += "```\n"

    # 2. SEEDS AND GEAR GRIDS WITH EXACT SHRUNK ROW SPACING
    seeds_table = "```diff\n=== SEEDS RESTOCK ESTIMATES ===\n"
    gear_table = "```diff\n=== GEARS RESTOCK ESTIMATES ===\n"
    
    seed_keys = ["Carrot", "Strawberry", "Blueberry", "Tulip", "Tomato", "Apple", "Bamboo", "Corn", "Cactus", "Pineapple", "Mushroom", "Green Bean", "Banana", "Grape", "Coconut", "Mango", "Dragon Fruit", "Acorn", "Cherry", "Sunflower", "Venus Fly Trap", "Pomegranate", "Poison Apple", "Venom Splitter", "Moon Bloom", "Dragon's Breath"]

    for item, base_chance in ALL_ITEMS_ODDS.items():
        if item in in_stock_list:
            time_str = "ACTIVE NOW"
            chance_str = "100%"
            prefix = "+ "
        elif item in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][item])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            # Calculate countdown window based on expected frequency
            expected_interval_minutes = round((100 / base_chance) * 5)
            minutes_remaining = max(5, expected_interval_minutes - minutes_since)
            
            # Immediate next 5-min reset probability calculation
            chance_of_missing = 1 - (base_chance / 100)
            accumulated_odds = (1 - (chance_of_missing ** max(1, rotations_missed))) * 100
            
            time_str = f"{minutes_remaining}m"
            chance_str = f"{accumulated_odds:.1f}%"
            prefix = "- " if accumulated_odds > 75 else "  "
        else:
            time_str = "No Data"
            chance_str = f"{base_chance}%"
            prefix = "  "

        row = f"{prefix}{item:<22} | Next: {time_str:<9} | Odds: {chance_str}\n"
        
        if item in seed_keys:
            seeds_table += row
        else:
            gear_table += row

    seeds_table += "```"
    gear_table += "```"

    msg1 = await channel.send(stock_text)
    msg2 = await channel.send(seeds_table)
    msg3 = await channel.send(gear_table)
    
    active_messages.extend([msg1, msg2, msg3])

# --- FIXED CARD-ISOLATION SCRAPER LOOP ---
@tasks.loop(seconds=60)
async def sixty_second_clock_loop():
    global active_messages
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    try:
        req = urllib.request.Request('https://growagarden2stock.com', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        found_items = []
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # FIX: Find every element box that represents a card container
        # This isolates individual grids so text doesn't bleed together
        for card in soup.find_all(['div', 'section']):
            card_text = card.get_text().lower()
            
            # STRICT GUARD: This card container MUST explicitly say 'in stock' to pass [INDEX 0.1.10]
            if "in stock" in card_text:
                for item in ALL_ITEMS_ODDS.keys():
                    if item.lower() in card_text:
                        if item not in found_items:
                            found_items.append(item)
                            memory["last_seen"][item] = now_utc

        memory["current_stock"] = found_items
        save_data()

    except Exception as e:
        print(f"Web Scraper Connection Error: {e}")

    # Wipe and reprint high-density board layers
    for old_msg in active_messages:
        try: await old_msg.delete()
        except: pass
    active_messages.clear()
    
    await generate_compact_dashboard(channel)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)
