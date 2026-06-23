import discord
from discord.ext import commands
import datetime
import json
import os
import random
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

# COMBINED DATABASE WITH ALL SEED AND GEAR PERCENTAGES
ALL_ITEMS_ODDS = {
    # --- Common & Uncommon Seeds ---
    "Carrot": 15.0, "Strawberry": 12.0, "Blueberry": 10.0, "Tulip": 8.0, "Tomato": 8.0, "Apple": 7.0, 
    # --- Rare & Epic Seeds ---
    "Bamboo": 5.0, "Corn": 5.0, "Cactus": 4.5, "Pineapple": 4.0, "Mushroom": 3.5, "Green Bean": 3.5, 
    "Banana": 3.0, "Grape": 3.0, "Coconut": 2.5, "Mango": 2.5, 
    # --- Legendary, Mythic & Super Seeds ---
    "Dragon Fruit": 2.0, "Acorn": 1.5, "Cherry": 1.5, "Sunflower": 1.2, "Venus Fly Trap": 1.0, 
    "Pomegranate": 1.0, "Poison Apple": 3.0, "Venom Splitter": 2.5, "Moon Bloom": 1.0, "Dragon's Breath": 0.5,
    # --- Gear Shop Items ---
    "Common Watering Can": 15.0, "Speed Mushroom": 8.0, "Uncommon Sprinkler": 6.0,
    "Rare Sprinkler": 3.0, "Epic Sprinkler": 1.5, "Legendary Sprinkler": 0.5
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
    print('Predictor Source-Verified Core is live on Render!')

# --- STRIP-MINING DATA HUB (SOURCE CHANNEL ID LOCKED) ---
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
                text_to_scan += message.content.title()
            if message.embeds:
                for embed in message.embeds:
                    if embed.title: text_to_scan += " " + embed.title.title()
                    if embed.description: text_to_scan += " " + embed.description.title()
                    for field in embed.fields:
                        text_to_scan += " " + field.name.title() + " " + field.value.title()

            found_items = []
            for item in ALL_ITEMS_ODDS.keys():
                if item in text_to_scan:
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
    item = item_name.strip().title()
    if item not in ALL_ITEMS_ODDS: return
    memory["last_seen"][item] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_data()
    await ctx.send(f"📥 **Manual Log Saved:** **{item}** locked.")

@bot.command(name="predict")
async def check_odds(ctx):
    if ctx.channel.id != CHANNEL_ID: return
    now = datetime.datetime.now(datetime.timezone.utc)
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (NEXT 5 MINS)** 🔮\n\n"
    
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
        if len(response_msg) > 1600:
            await ctx.send(response_msg)
            response_msg = ""
            
    if response_msg: await ctx.send(response_msg)

@bot.command(name="predict24h")
async def predict_24_hours(ctx):
    if ctx.channel.id != CHANNEL_ID: return
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
        if count <= 16: embed1.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        else: embed2.add_field(name=f"🔹 {item}", value=f"⏱️ {display_times}", inline=False)
        
    await ctx.send(embed=embed1)
    await ctx.send(embed=embed2)

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)

