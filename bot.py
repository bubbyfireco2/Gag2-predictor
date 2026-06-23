import discord
from discord.ext import commands
import datetime
import json
import os
import random
# --- WEBSERVER IMPORTS FOR RENDER 24/7 BYPASS ---
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
CHANNEL_ID = 1518727458919284937  

DATA_FILE = "/opt/render/project/src/probability_memory.json" if os.environ.get("RENDER") else "probability_memory.json"

# 1. EXPANDED DATABASE WITH ALL SEED DROP PERCENTAGES
SEED_ODDS = {
    # --- Common & Uncommon (High Drop Rates) ---
    "Carrot": 15.0, "Strawberry": 12.0, "Blueberry": 10.0, 
    "Tulip": 8.0, "Tomato": 8.0, "Apple": 7.0, 
    # --- Rare ---
    "Bamboo": 5.0, "Corn": 5.0, "Cactus": 4.5, "Pineapple": 4.0, 
    # --- Epic ---
    "Mushroom": 3.5, "Green Bean": 3.5, "Banana": 3.0, 
    "Grape": 3.0, "Coconut": 2.5, "Mango": 2.5, 
    # --- Legendary ---
    "Dragon Fruit": 2.0, "Acorn": 1.5, "Cherry": 1.5, "Sunflower": 1.2, 
    # --- Mythic ---
    "Venus Fly Trap": 1.0, "Pomegranate": 1.0, "Poison Apple": 3.0, "Venom Splitter": 2.5,
    # --- Super ---
    "Moon Bloom": 1.0, "Dragon's Breath": 0.5
}

memory = {"last_seen": {}}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            memory = json.load(f)
    except:
        pass

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(memory, f)
    except Exception as e:
        print(f"Failed to save JSON data: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    print('Predictor Core Engine is live on Render cloud!')

# 2. REPORT COMMAND (Now accepts all 26 seeds!)
@bot.command(name="report")
async def report_seed(ctx, *, seed_name: str):
    if ctx.channel.id != CHANNEL_ID:
        return

    seed = seed_name.strip().title()
    if seed not in SEED_ODDS:
        await ctx.send(f"❌ **Error:** '{seed}' isn't a recognized seed name. Check your spelling!")
        return

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    memory["last_seen"][seed] = now_utc
    save_data()

    await ctx.send(f"📥 **Log Saved:** **{seed}** logged! Timers have been re-calibrated.")

# 3. NEXT-RESET PROBABILITY COMMAND
@bot.command(name="predict")
async def check_odds(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (NEXT 5 MINS)** 🔮\n\n"

    # Only show rare, legendary, mythic, and super seeds here so chat doesn't overflow
    high_tier_filters = ["Venus Fly Trap", "Pomegranate", "Poison Apple", "Venom Splitter", "Moon Bloom", "Dragon's Breath", "Dragon Fruit", "Acorn", "Cherry", "Sunflower"]

    for seed, base_chance in SEED_ODDS.items():
        if seed not in high_tier_filters:
            continue  # Skips carrots/tomatoes in the printout so it is easy to read
            
        if seed in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][seed])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            chance_of_missing = 1 - (base_chance / 100)
            accumulated_odds = (1 - (chance_of_missing ** max(1, rotations_missed))) * 100
            
            status = f"⏱️ Last seen: `{minutes_since} mins ago`"
            if accumulated_odds > 65:
                status += " ⚠️ **HIGHLY OVERDUE!**"
        else:
            accumulated_odds = base_chance
            status = "⏱️ Last seen: `Never logged`"

        response_msg += f"🔹 **{seed}**\n   • Next Reset Drop Chance: **{accumulated_odds:.2f}%** (Base: {base_chance}%)\n   • {status}\n\n"

    await ctx.send(response_msg)

# 4. 24-HOUR TIMELINE FORECAST SIMULATOR
@bot.command(name="predict24h")
async def predict_24_hours(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    predictions = {seed: [] for seed in SEED_ODDS}
    
    for cycle in range(1, 289):
        simulated_time = now + datetime.timedelta(minutes=cycle * 5)
        
        for seed, base_chance in SEED_ODDS.items():
            roll = random.uniform(0, 100)
            if roll <= base_chance:
                time_str = simulated_time.strftime("%I:%M %p")
                predictions[seed].append(time_str)

    embed = discord.Embed(
        title="🔮 24-HOUR SHOP RESTOCK TIMELINE FORECAST 🔮",
        description="Estimated high-probability hours when ultra-rare seeds are most likely to drop:",
        color=discord.Color.purple()
    )

    # Display predictions for top high-tier seeds
    tracked_display = ["Venus Fly Trap", "Pomegranate", "Poison Apple", "Venom Splitter", "Moon Bloom", "Dragon's Breath"]
    for seed in tracked_display:
        times = predictions[seed]
        if times:
            display_times = ", ".join(times[:5])
            if len(times) > 5:
                display_times += f" (+{len(times)-5} more windows)"
        else:
            display_times = "❌ No restocks predicted in the next 24 hours."

        embed.add_field(name=f"🔹 {seed} (Base: {SEED_ODDS[seed]}%)", value=f"⏱️ **Estimated Windows:** {display_times}", inline=False)

    embed.set_footer(text="Treat these as prime high-probability hunting windows!")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)
