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
SOURCE_CHANNEL_ID = 1481858257793585255  # The external notifier channel ID you provided!

DATA_FILE = "/opt/render/project/src/probability_memory.json" if os.environ.get("RENDER") else "probability_memory.json"

# COMBINED DATABASE WITH ALL TRUE SEEDS AND YOUR CORRECTED GEAR LIST
ALL_ITEMS_ODDS = {
    # --- Seeds ---
    "Carrot": 15.0, "Strawberry": 12.0, "Blueberry": 10.0, "Tulip": 8.0, "Tomato": 8.0, "Apple": 7.0, 
    "Bamboo": 5.0, "Corn": 5.0, "Cactus": 4.5, "Pineapple": 4.0, "Mushroom": 3.5, "Green Bean": 3.5, 
    "Banana": 3.0, "Grape": 3.0, "Coconut": 2.5, "Mango": 2.5, "Dragon Fruit": 2.0, "Acorn": 1.5, 
    "Cherry": 1.5, "Sunflower": 1.2, "Venus Fly Trap": 1.0, "Pomegranate": 1.0, "Poison Apple": 3.0, 
    "Venom Splitter": 2.5, "Moon Bloom": 1.0, "Dragon's Breath": 0.5,
    
    # --- Grow a Garden 2 Gear List ---
    "Common Sprinkler": 12.0, "Uncommon Sprinkler": 8.0, "Rare Sprinkler": 4.0,
    "Legendary Sprinkler": 1.0, "Super Sprinkler": 0.5, "Common Watering Can": 15.0,
    "Super Watering Can": 1.0, "Trowel": 10.0, "Jump Mushroom": 6.0, "Speed Mushroom": 6.0,
    "Supersize Mushroom": 4.0, "Invisibility Mushroom": 3.0, "Shrink Mushroom": 4.0,
    "Gnome": 5.0, "Basic Pot": 12.0, "Flashbang": 5.0
}

memory = {"last_seen": {}}

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
    print('Predictor Core Engine is live on Render cloud!')

# --- AUTOMATIC DATA EXTRACTION HUB ---
@bot.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID:
        is_from_source = False
        if message.reference and message.reference.channel_id == SOURCE_CHANNEL_ID:
            is_from_source = True
        elif message.flags.value & 256:
            is_from_source = True
            
        if is_from_source:
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
            # Reworked scanner: Finds items even if they contain punctuation, numbers, or tags
            for item in ALL_ITEMS_ODDS.keys():
                if item.lower() in text_to_scan:
                    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    memory["last_seen"][item] = now_utc
                    found_items.append(item)

            if found_items:
                save_data()
                print(f"[SOURCE VERIFIED] Auto-logged: {', '.join(found_items)}")

    await bot.process_commands(message)

@bot.command(name="report")
async def report_item(ctx, *, item_name: str):
    if ctx.channel.id != CHANNEL_ID: return
    try: await ctx.message.delete()
    except: pass
    
    item = item_name.strip().title()
    if item not in ALL_ITEMS_ODDS: return
    memory["last_seen"][item] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_data()
    msg = await ctx.send(f"📥 **Manual Log Saved:** **{item}** locked.")
    await asyncio.sleep(10)
    try: await msg.delete()
    except: pass

@bot.command(name="predict")
async def check_odds(ctx):
    if ctx.channel.id != CHANNEL_ID: return
    
    # FIXED BUG 1: Instantly deletes your prompt before compiling data
    try: await ctx.message.delete()  
    except: pass
    
    now = datetime.datetime.now(datetime.timezone.utc)
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (IMMEDIATE NEXT RESET)** 🔮\n\n"
    sent_messages = []
    
    for item, base_chance in ALL_ITEMS_ODDS.items():
        if item in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][item])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            # FIXED MATHEMATICS: Displays pure single-cycle probability values
            chance_of_missing = 1 - (base_chance / 100)
            accumulated_odds = (1 - (chance_of_missing ** max(1, rotations_missed))) * 100
            
            status = f"⏱️ Last seen: `{minutes_since} mins ago`"
            if accumulated_odds > 75: status += " ⚠️ **HIGHLY OVERDUE!**"
        else:
            accumulated_odds = base_chance
            status = "⏱️ Last seen: `Never logged`"
            
        response_msg += f"🔹 **{item}**\n   • Next 5-Min Drop Chance: **{accumulated_odds:.2f}%**\n   • {status}\n\n"
        if len(response_msg) > 1500:
            msg = await ctx.send(response_msg)
            sent_messages.append(msg)
            response_msg = ""
            
    if response_msg: 
        msg = await ctx.send(response_msg)
        sent_messages.append(msg)
        
    # Schedule background wipe task
    await asyncio.sleep(300)
    for msg in sent_messages:
        try: await msg.delete()
        except: pass

@bot.command(name="predict24h")
async def predict_24_hours(ctx):
    if ctx.channel.id != CHANNEL_ID: return
    try: await ctx.message.delete()  
    except: pass
    
    now = datetime.datetime.now(datetime.timezone.utc)
    predictions = {item: [] for item in ALL_ITEMS_ODDS}
    
    for cycle in range(1, 289):
        simulated_time = now + datetime.timedelta(minutes=cycle * 5)
        for item, base_chance in ALL_ITEMS_ODDS.items():
            roll = random.uniform(0, 100)
            if roll <= base_chance:
                predictions[item].append(simulated_time.strftime("%I:%M %p"))
                
    embed1 = discord.Embed(title="🔮 24-HOUR SHOP TIMELINE (PART 1) 🔮", color=discord.Color.purple())
    embed2 = discord.Embed(title="🔮 24-HOUR SHOP TIMELINE (PART 2) 🔮", color=discord.Color.purple())
    count = 0
    for item, times in predictions.items():
        count += 1
        display_times = ", ".join(times[:4]) if times else "❌ No restocks predicted."
        if len(times) > 4: display_times += f" (+{len(times)-4} more)"
        if count <= 21: embed1.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        else: embed2.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        
    msg1 = await ctx.send(embed=embed1)
    msg2 = await ctx.send(embed=embed2)
    
    await asyncio.sleep(300)
    try: await msg1.delete()
    except: pass
    try: await msg2.delete()
    except: pass

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)

