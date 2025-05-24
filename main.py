import os
from datetime import datetime, timedelta

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ==== BOT SETUP ====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ==== GENERÁTOR DAT ====
def generate_weekdays():
    today = datetime.today()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return [(next_monday + timedelta(days=i)).strftime("%A %d.%m.") for i in range(5)]


# ==== ODESLÁNÍ ANKETY ====
async def send_poll(channel: discord.abc.Messageable):
    options = generate_weekdays()

    poll = discord.Poll(
        question="Kdy můžete příští týden?",
        multiple=True,
        duration=timedelta(days=7)
    )
    for answer in options:
        poll.add_answer(text=answer)

    await channel.send(poll=poll)


# ==== ON READY ====
@bot.event
async def on_ready():
    print(f"Přihlášen jako {bot.user}")

    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Slash příkazy synchronizovány: {len(synced)}")
    except Exception as e:
        print(f"Chyba při synchronizaci slash příkazů: {e}")

    scheduler = AsyncIOScheduler()
    now = datetime.now()
    scheduler.add_job(
        auto_create_poll,
        "cron",
        day_of_week="sat",
        hour=now.hour,
        minute=(now.minute + 1) % 60
    )
    # scheduler.add_job(auto_create_poll, "cron", day_of_week="sat", hour=17, minute=30)
    scheduler.start()


# ==== AUTOMATICKÁ ANKETA ====
async def auto_create_poll():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await send_poll(channel)
    else:
        print("⚠️ Kanál nenalezen (CHANNEL_ID může být špatně).")


# ==== SLASH PŘÍKAZ /pollnow ====
@bot.tree.command(name="pollnow", description="Ručně vytvoří anketu pro příští týden")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def pollnow(interaction: discord.Interaction):
    await interaction.response.defer(thinking=False)
    await send_poll(interaction.channel)
    await interaction.followup.send("@everyone", ephemeral=True)


# ==== START ====
bot.run(TOKEN)
