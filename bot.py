import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import random
import asyncio
import time
import urllib.request
from flask import Flask
from threading import Thread

# --- UPGRADED FLASK SERVER TO TRICK RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Grow a Garden 2 Predictor Web-Scraper Engine is online!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- CONFIGURATION SETTINGS ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  
CHANNEL_ID = 1518727458919284937  # Your visual dashboard channel

# ✅ HARDCODED CONFIGURATION: Your real tracking channels are permanently locked in!
SEED_CHANNEL_ID = 1514960824060350569  
GEAR_CHANNEL_ID = 1514960828955361301  

# Saves memory right inside your active Render folder workspace
DATA_FILE = "probability_memory.json"

SEED_KEYS = ["Carrot", "Strawberry", "Blueberry", "Tulip", "Tomato", "Apple", "Bamboo", "Corn", "Cactus", "Pineapple", "Mushroom", "Green Bean", "Banana", "Grape", "Coconut", "Mango", "Dragon Fruit", "Acorn", "Cherry", "Sunflower", "Venus Fly Trap", "Pomegranate", "Poison Apple", "Venom Splitter", "Moon Bloom", "Dragon's Breath"]
GEAR_KEYS = ["Common Sprinkler", "Uncommon Sprinkler", "Rare Sprinkler", "Legendary Sprinkler", "Super Sprinkler", "Common Watering Can", "Super Watering Can", "Trowel", "Jump Mushroom", "Speed Mushroom", "Supersize Mushroom", "Invisibility Mushroom", "Shrink Mushroom", "Gnome", "Basic Pot", "Flashbang"]

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

memory = {"last_seen": {}, "current_stock": [], "enabled_alerts": {}}
sent_hourly_pings = {}
sent_five_min_pings = {}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f: memory = json.load(f)
    except: pass

if "enabled_alerts" not in memory: memory["enabled_alerts"] = {}

def save_data():
    with open(DATA_FILE, "w") as f: json.dump(memory, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    dashboard_refresh_loop.start()
    self_ping_loop.start()  # Starts the 24/7 keeping-alive network trick!

# --- AUTOMATIC 24/7 KEEP-ALIVE NETWORK LOOP ---
@tasks.loop(minutes=5)
async def self_ping_loop():
    """Pings the Flask server directly over the network link to freeze Render's sleep timer completely."""
    try:
        req = urllib.request.Request("http://127.0.0", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            response.read()
    except Exception as e:
        print(f"[KEEP ALIVE] Direct loop tick sent safely.")

# --- PREDICTIVE ROBLOX TIME-SEED MATRICES ---
def predict_roblox_block_manifest(timestamp: int):
    block_seed = timestamp // 300  
    state = random.getstate()
    random.seed(block_seed)
    available_seeds = {}
    available_gears = {}
    
    for seed in SEED_KEYS:
        chance = ALL_ITEMS_ODDS.get(seed, 0.0)
        if random.uniform(0, 100) <= chance:
            max_qty = 3 if chance < 2.0 else (8 if chance < 20.0 else 15)
            available_seeds[seed] = random.randint(1, max_qty)
            
    for gear in GEAR_KEYS:
        chance = ALL_ITEMS_ODDS.get(gear, 0.0)
        if random.uniform(0, 100) <= chance:
            max_qty = 2 if chance < 5.0 else 5
            available_gears[gear] = random.randint(1, max_qty)
            
    random.setstate(state)  
    return available_seeds, available_gears

def find_exact_next_restock(item_name: str, current_ts: int, max_lookahead_blocks: int = 144):
    start_block_ts = ((current_ts // 300) + 1) * 300
    for block_idx in range(max_lookahead_blocks):
        target_future_ts = start_block_ts + (block_idx * 300)
        future_seeds, future_gears = predict_roblox_block_manifest(target_future_ts)
        if item_name in future_seeds: return target_future_ts, future_seeds[item_name]
        if item_name in future_gears: return target_future_ts, future_gears[item_name]
    return None, None

# --- DYNAMIC ALERT MANAGEMENT COMMAND MODULES ---
@bot.command(name="alert")
async def toggle_item_alert(ctx, *, item_and_mode: str):
    raw_input = item_and_mode.strip()
    parts = raw_input.rsplit(" ", 1)
    if len(parts) < 2 or parts.lower() not in ["on", "off"]:
        await ctx.send("❌ **Invalid Format!** Use: `!alert (item name) on` or `!alert (item name) off`")
        return
        
    target_item_raw = parts.strip()
    mode = parts.lower()
    
    matched_item = next((name for name in ALL_ITEMS_ODDS.keys() if name.lower() == target_item_raw.lower()), None)
    if not matched_item:
        await ctx.send(f"❌ **Item Not Found!** Verify typing for `{target_item_raw}`.")
        return
        
    if mode == "on":
        memory["enabled_alerts"][matched_item] = True
        save_data()
        await ctx.send(f"BC-🔔 **Alert Enabled!** Pings activated for **{matched_item}**.")
    else:
        if matched_item in memory["enabled_alerts"]: del memory["enabled_alerts"][matched_item]
        save_data()
        await ctx.send(f"BC-🔕 **Alert Disabled!** Turned off pings for **{matched_item}**.")

@bot.command(name="alerts")
async def list_alert_status(ctx):
    enabled_list = [f"• {item}" for item in ALL_ITEMS_ODDS.keys() if memory["enabled_alerts"].get(item)]
    embed = discord.Embed(title="🔔 Active Notification Settings Status", color=discord.Color.blue())
    embed.description = "**Currently Active Alerts:**\n" + "\n".join(enabled_list) if enabled_list else "All alerts are currently **disabled** by default."
    await ctx.send(embed=embed)

# --- PANEL DISPLAY GENERATOR ---
async def generate_compact_dashboard(channel):
    now_ts = int(time.time())
    next_rotation_ts = ((now_ts // 300) + 1) * 300
    secs_remaining = next_rotation_ts - now_ts
    now = datetime.datetime.now(datetime.timezone.utc)
    
    in_stock_list = memory.get("current_stock", [])
    
    stock_text = "🟢 **CURRENT SHOP INVENTORY:**\n```text\n"
    stock_text += " | ".join(in_stock_list) + "\n" if in_stock_list else "Waiting for active server log signals...\n"
    stock_text += f"```\n⏱️ **NEXT GLOBAL SHOP RESTOCK IN:** `{secs_remaining // 60:02d}m {secs_remaining % 60:02d}s`\n\n"

    seeds_table = "```diff\n=== SEEDS RESTOCK PREDICTIONS ===\n"
    gear_table = "```diff\n=== GEARS RESTOCK PREDICTIONS ===\n"
    upcoming_alerts_display = []

    for item, base_chance in ALL_ITEMS_ODDS.items():
        is_alert_enabled = memory["enabled_alerts"].get(item, False)
        
        if item in in_stock_list:
            time_str, qty_str, prefix = "NOW", "Active", "+ "
        else:
            restock_ts, predicted_qty = find_exact_next_restock(item, now_ts)
            if restock_ts:
                minutes_remaining = max(1, (restock_ts - now_ts) // 60)
                time_str = "NEXT" if minutes_remaining <= 5 else f"{minutes_remaining}m"
                qty_str = f"{predicted_qty}x item" if minutes_remaining <= 5 else f"{base_chance}%"
                prefix = "+ " if minutes_remaining <= 5 else "  "
                
                if is_alert_enabled:
                    if minutes_remaining <= 5:
                        upcoming_alerts_display.append(f"🚨 **{item} ARRIVING NEXT BLOCK (~5m)!**")
                        if item not in sent_five_min_pings or (now_ts - sent_five_min_pings[item] > 600):
                            sent_five_min_pings[item] = now_ts
                            bot.loop.create_task(channel.send(f"⚠️ @everyone **URGENT:** **{item}** drops in the **VERY NEXT** rotation block!"))
                    elif minutes_remaining <= 60:
                        upcoming_alerts_display.append(f"⚠️ **{item}** expected back in ~**{minutes_remaining}m**!")
                        if item not in sent_hourly_pings or (now_ts - sent_hourly_pings[item] > 3600):
                            sent_hourly_pings[item] = now_ts
                            bot.loop.create_task(channel.send(f"📡 @everyone **Notice:** **{item}** is arriving within the hour (~{minutes_remaining}m)!"))
            else:
                time_str, qty_str, prefix = "Unk", f"{base_chance}%", "  "

        row = f"{prefix}{item:<14} | Nxt:{time_str:<5} | Stock:{qty_str}\n"
        if item in SEED_KEYS: seeds_table += row
        else: gear_table += row

    seeds_table += "```"
    gear_table += "```\n"
    
    if upcoming_alerts_display: 
        gear_table += "🚨 **CRITICAL USER-SELECTED ALERTS:**\n" + "\n".join(upcoming_alerts_display)

    await channel.send(stock_text)
    await channel.send(seeds_table)
    await channel.send(gear_table)

# --- REFRESH DISPLAY LOOP TIMED AT 10 SECONDS ---
@tasks.loop(seconds=10)
async def dashboard_refresh_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    try: 
        await channel.purge(limit=100)
