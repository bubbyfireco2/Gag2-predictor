import discord
from discord.ext import commands
import datetime
import json
import os
import random

# --- CONFIGURATION SETTINGS ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Hidden securely via Render vault
CHANNEL_ID = 1518727458919284937  # Your verified Discord channel ID

DATA_FILE = "probability_memory.json"

# 1. FIXED GAME PERCENTAGES 
SEED_ODDS = {
    "Dragon's Breath": 0.5,    # 0.5% ultra rare chance
    "Moon Bloom": 1.0,         # 1.0% chance
    "Venom Splitter": 2.5,     # 2.5% chance
    "Poison Apple": 3.0        # 3.0% chance
}

memory = {"last_seen": {}}

# Load database from system storage automatically
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            memory = json.load(f)
    except:
        pass

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(memory, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    print('Predictor Core Engine is live on Render cloud!')

# 2. REPORT COMMAND (Logs drops to calibrate prediction clocks)
@bot.command(name="report")
async def report_seed(ctx, *, seed_name: str):
    if ctx.channel.id != CHANNEL_ID:
        return

    seed = seed_name.strip().title()
    if seed not in SEED_ODDS:
        await ctx.send(f"❌ I am only tracking: {', '.join(SEED_ODDS.keys())}")
        return

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    memory["last_seen"][seed] = now_utc
    save_data()

    await ctx.send(f"📥 **Log Saved:** **{seed}** logged! Re-calculating the 24-hour forecast timelines...")

# 3. NEXT-RESET PROBABILITY COMMAND
@bot.command(name="predict")
async def check_odds(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    response_msg = "🔮 **LIVE SHOP SPAWN PROBABILITIES (NEXT 5 MINS)** 🔮\n\n"

    for seed, base_chance in SEED_ODDS.items():
        if seed in memory["last_seen"]:
            last_time = datetime.datetime.fromisoformat(memory["last_seen"][seed])
            minutes_since = int((now - last_time).total_seconds() / 60)
            rotations_missed = minutes_since // 5
            
            # Compound missing logic math calculation
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
    
    # Run a 24-hour simulation loop (288 cycles of 5-minute intervals)
    for cycle in range(1, 289):
        simulated_time = now + datetime.timedelta(minutes=cycle * 5)
        
        for seed, base_chance in SEED_ODDS.items():
            roll = random.uniform(0, 100)
            if roll <= base_chance:
                time_str = simulated_time.strftime("%I:%M %p")
                predictions[seed].append(time_str)

    embed = discord.Embed(
        title="🔮 24-HOUR SHOP RESTOCK TIMELINE FORECAST 🔮",
        description="Estimated high-probability hours when rare seeds are most likely to drop over the next 24 hours:",
        color=discord.Color.purple()
    )

    for seed, times in predictions.items():
        if times:
            display_times = ", ".join(times[:5])
            if len(times) > 5:
                display_times += f" (+{len(times)-5} more windows)"
        else:
            display_times = "❌ No restocks predicted in the next 24 hours."

        embed.add_field(name=f"🔹 {seed} (Chance: {SEED_ODDS[seed]}%)", value=f"⏱️ **Estimated Windows:** {display_times}", inline=False)

    embed.set_footer(text="Treat these as prime high-probability hunting windows!")
    await ctx.send(embed=embed)

bot.run(TOKEN)
