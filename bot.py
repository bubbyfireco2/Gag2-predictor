import discord
from discord.ext import commands
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
CHANNEL_ID = 1518727458919284937  # Your personal alert channel ID where the tracker mirrors

DATA_FILE = "/opt/render/project/src/probability_memory.json" if os.environ.get("RENDER") else "probability_memory.json"

# COMBINED DATABASE WITH ALL GAINESVILLE SEEDS AND GEARS
ALL_ITEMS_ODDS = {
    "Carrot": 15.0, "Strawberry": 12.0, "Blueberry": 10.0, "Tulip": 8.0, "Tomato": 8.0, "Apple": 7.0, 
    "Bamboo": 5.0, "Corn": 5.0, "Cactus": 4.5, "Pineapple": 4.0, "Mushroom": 3.5, "Green Bean": 3.5, 
    "Banana": 3.0, "Grape": 3.0, "Coconut": 2.5, "Mango": 2.5, "Dragon Fruit": 2.0, "Acorn": 1.5, 
    "Cherry": 1.5, "Sunflower": 1.2, "Venus Fly Trap": 1.0, "Pomegranate": 1.0, "Poison Apple": 3.0, 
    "Venom Splitter": 2.5, "Moon Bloom": 1.0, "Dragon's Breath": 0.5,
    "Common Sprinkler": 12.0, "Uncommon Sprinkler": 8.0, "Rare Sprinkler": 4.0,
    "Legendary Sprinkler": 1.0, "Super Sprinkler": 0.5, "Common Watering Can": 15.0,
    "Super Watering Can": 1.0, "Trowel": 10.0, "Jump Mushroom": 6.0, "Speed Mushroom": 6.0,
    "Supersize Mushroom": 4.0, "Invisibility Mushroom": 3.0, "Shrink Mushroom": 4.0,
    "Gnome": 5.0, "Basic Pot": 12.0, "Flashbang": 5.0
}

# ROLE ID DICTIONARY MAPPER (Extracts names directly out of your role number tags!)
ROLE_MAP = {
    "1515663877201727618": "Strawberry",
    "1515663876732096582": "Blueberry",
    "1515443219658309703": "Tulip",
    "1515437833312272424": "Tomato",
    "1515663875645902888": "Bamboo",
    "1515437073211850922": "Carrot",
    "1515438866675400775": "Apple",
    "1515441615563653291": "Dragon Fruit",
    "1515669111277879377": "Uncommon Sprinkler",
    "1515663875943436338": "Mushroom",
    "1515663877608570900": "Basic Pot",
    "1515438868952776794": "Flashbang"
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
    print('Role-Decoder Automated Predictor is live!')

async def run_auto_predictions(channel):
    global active_predictions
    now = datetime.datetime.now(datetime.timezone.utc)
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (NEXT RESTOCK WINDOW)** 🔮\n\n"
    
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

async def run_auto_24h_forecast(channel):
    global active_embeds
    now = datetime.datetime.now(datetime.timezone.utc)
    predictions = {item: [] for item in ALL_ITEMS_ODDS}
    
    for cycle in range(1, 289):
        simulated_time = now + datetime.timedelta(minutes=cycle * 5)
        for item, base_chance in ALL_ITEMS_ODDS.items():
            roll = random.uniform(0, 100)
            if roll <= base_chance:
                predictions[item].append(simulated_time.strftime("%I:%M %p"))
                
    embed1 = discord.Embed(title="🔮 AUTOMATED 24-HOUR FORECAST TIMELINE (PART 1) 🔮", color=discord.Color.purple())
    embed2 = discord.Embed(title="🔮 AUTOMATED 24-HOUR FORECAST TIMELINE (PART 2) 🔮", color=discord.Color.purple())
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

# --- ADVANCED CROWD-SOURCE AUTO LOGGER ---
@bot.event
async def on_message(message):
    global active_predictions, active_embeds
    
    if message.channel.id == CHANNEL_ID:
        text_to_scan = ""
        if message.content:
            text_to_scan += " " + message.content.lower()
        if message.embeds:
            for embed in message.embeds:
                if embed.title: text_to_scan += " " + embed.title.lower()
                if embed.description: text_to_scan += " " + embed.description.lower()
                for field in embed.fields:
                    text_to_scan += " " + field.name.lower() + " " + field.value.lower()

        found_items = []

        # 1. EXTRACT FROM ROLE IDs (The long numbers from your clipboard text!)
        for role_id, item_name in ROLE_MAP.items():
            if role_id in text_to_scan:
                if item_name not in found_items:
                    found_items.append(item_name)

        # 2. BACKUP EXTRACT FROM TEXT CHUNKS
        for item in ALL_ITEMS_ODDS.keys():
            if item.lower() in text_to_scan:
                if item not in found_items:
                    found_items.append(item)

        # Special generic item fallback mappings
        if "mushroom" in text_to_scan and "mushroom" not in [f.lower() for f in found_items]:
            found_items.append("Mushroom")

        # TRIGGER AUTO UPDATE SYSTEM
        if found_items:
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for item in found_items:
                memory["last_seen"][item] = now_utc
            save_data()
            print(f"[ROLE SCANNER SUCCESS] Auto-logged: {', '.join(found_items)}")
            
            # Wipe older prediction blocks completely
            for old_msg in active_predictions + active_embeds:
                try: await old_msg.delete()
                except: pass
            active_predictions.clear()
            active_embeds.clear()
            
            # Wait 2 seconds and print fresh probabilities
            await asyncio.sleep(2)
            await run_auto_predictions(message.channel)
            await run_auto_24h_forecast(message.channel)

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)

