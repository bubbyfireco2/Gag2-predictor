import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import random
import asyncio
from flask import Flask
from threading import Thread

# --- MINIMAL FLASK SERVER TO TRICK RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Predictor Core Engine is online!"

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

# COMBINED DATABASE WITH YOUR ACCURATE REAL-GAME PERCENTAGES
ALL_ITEMS_ODDS = {
    # --- True Seeds ---
    "Carrot": 100.0, "Strawberry": 100.0, "Blueberry": 100.0, "Tulip": 100.0, "Tomato": 90.0, "Apple": 52.0, 
    "Bamboo": 80.0, "Corn": 25.0, "Cactus": 16.6, "Pineapple": 12.5, "Mushroom": 9.0, "Green Bean": 15.0, 
    "Banana": 9.0, "Grape": 6.6, "Coconut": 5.0, "Mango": 5.0, "Dragon Fruit": 4.0, "Acorn": 2.9, 
    "Cherry": 2.2, "Sunflower": 1.7, "Venus Fly Trap": 1.43, "Pomegranate": 0.9, "Poison Apple": 0.5, 
    "Venom Splitter": 0.475, "Moon Bloom": 0.35, "Dragon's Breath": 0.275,
    
    # --- True Gear List ---
    "Common Sprinkler": 50.0, "Uncommon Sprinkler": 35.0, "Rare Sprinkler": 25.0, "Legendary Sprinkler": 4.0, 
    "Super Sprinkler": 1.2, "Common Watering Can": 90.0, "Super Watering Can": 2.0, "Trowel": 28.0, 
    "Jump Mushroom": 24.0, "Speed Mushroom": 22.0, "Supersize Mushroom": 10.0, "Invisibility Mushroom": 4.0, 
    "Shrink Mushroom": 10.0, "Gnome": 8.0, "Basic Pot": 7.0, "Flashbang": 7.0
}

memory = {"last_seen": {}}
active_predictions = []
active_embeds = []

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f: memory = json.load(f)
    except: pass

def save_data():
    try:
        with open(DATA_FILE, "w") as f: json.dump(memory, f)
    except Exception as e: print(f"JSON Error: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    print('Clock-Synced Automated Predictor is live with real percentages!')
    clock_restock_checker_loop.start()

async def post_fresh_dashboards(channel):
    global active_predictions, active_embeds
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Compile 5-minute probabilities text block
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (IMMEDIATE NEXT WINDOW)** 🔮\n\n"
    for item, base_chance in ALL_ITEMS_ODDS.items():
        if item in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][item])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            chance_of_missing = 1 - (base_chance / 100)
            accumulated_odds = (1 - (chance_of_missing ** max(1, rotations_missed))) * 100
            
            status = f"⏱️ Last seen: `{minutes_since} mins ago`"
            if accumulated_odds > 75: status += " ⚠️ **HIGHLY OVERDUE!**"
        else:
            accumulated_odds = base_chance
            status = "⏱️ Last seen: `Never logged`"
            
        response_msg += f"🔹 **{item}**\n   • Next Reset Chance: **{accumulated_odds:.2f}%**\n   • {status}\n\n"
        if len(response_msg) > 1500:
            msg = await channel.send(response_msg)
            active_predictions.append(msg)
            response_msg = ""
    if response_msg: 
        msg = await channel.send(response_msg)
        active_predictions.append(msg)

    # 2. Compile 24-hour simulation embed charts
    predictions = {item: [] for item in ALL_ITEMS_ODDS}
    for cycle in range(1, 289):
        simulated_time = now + datetime.timedelta(minutes=cycle * 5)
        for item, base_chance in ALL_ITEMS_ODDS.items():
            if random.uniform(0, 100) <= base_chance:
                predictions[item].append(simulated_time.strftime("%I:%M %p"))
                
    embed1 = discord.Embed(title="🔮 AUTOMATED 24-HOUR FORECAST (PART 1) 🔮", color=discord.Color.purple())
    embed2 = discord.Embed(title="🔮 AUTOMATED 24-HOUR FORECAST (PART 2) 🔮", color=discord.Color.purple())
    count = 0
    for item, times in predictions.items():
        count += 1
        display_times = ", ".join(times[:4]) if times else "❌ No restocks predicted."
        if len(times) > 4: display_times += f" (+{len(times)-4} more)"
        if count <= 21: embed1.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        else: embed2.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        
    msg1 = await channel.send(embed=embed1)
    msg2 = await channel.send(embed=embed2)
    active_embeds.extend([msg1, msg2])

# --- STRICT 5-MINUTE CLOCK-TICK DETECTOR ---
@tasks.loop(seconds=10)
async def clock_restock_checker_loop():
    global active_predictions, active_embeds
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Triggers precisely on integers of 5 (e.g., :00, :05, :10, :15, etc.)
    if now.minute % 5 == 0 and now.second < 15:
        print(f"[CLOCK MATCH] Restock window hit at {now.strftime('%H:%M:%S')}")
        
        # Instantly wipe previous charts
        for old_msg in active_predictions + active_embeds:
            try: await old_msg.delete()
            except: pass
        active_predictions.clear()
        active_embeds.clear()
        
        await asyncio.sleep(2)
        await post_fresh_dashboards(channel)

# --- INCOMING DATA LOG INTERCEPTOR ---
@bot.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID:
        if message.author.id == bot.user.id: return

        text_to_scan = ""
        if message.content: text_to_scan += " " + message.content.lower()
        if message.embeds:
            for embed in message.embeds:
                if embed.title: text_to_scan += " " + embed.title.lower()
                if embed.description: text_to_scan += " " + embed.description.lower()
                for field in embed.fields:
                    text_to_scan += " " + field.name.lower() + " " + field.value.lower()

        found_items = []
        if "mushroom" in text_to_scan: found_items.append("Mushroom")

        for item in ALL_ITEMS_ODDS.keys():
            if item.lower() in text_to_scan:
                if item not in found_items: found_items.append(item)

        if found_items:
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for item in found_items:
                memory["last_seen"][item] = now_utc
            save_data()
            print(f"[TIMING SEED] Locked live restock timestamp for: {', '.join(found_items)}")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)

