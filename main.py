import os
from datetime import datetime, timedelta, date

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
def generate_days():
    today = datetime.today()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    include_days = [1, 2, 4, 5, 6]  # Út, St, Pá, So, Ne
    return [
        (next_monday + timedelta(days=i)).strftime("%A %d.%m.")
        for i in include_days
    ]


# ==== ODESLÁNÍ ANKETY ====
async def send_poll(channel: discord.abc.Messageable):
    options = generate_days()

    poll = discord.Poll(
        question="Kdy můžete příští týden?",
        multiple=True,
        duration=timedelta(days=7)
    )
    for answer in options:
        poll.add_answer(text=answer)

    await channel.send(content="@everyone", poll=poll)


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
    scheduler.add_job(auto_create_poll, "cron", day_of_week="mon", hour=20)
    scheduler.start()


def is_target_week():
    reference = date(2025, 5, 26)
    today = date.today()
    weeks_since = (today - reference).days // 7
    return weeks_since % 2 == 0


# ==== AUTOMATICKÁ ANKETA ====
async def auto_create_poll():
    if not is_target_week():
        print("⏭ Tento týden není cílový (běží jednou za 2 týdny).")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await send_poll(channel)
    else:
        print("⚠️ Kanál nenalezen (CHANNEL_ID může být špatně).")


@bot.tree.command(name="pollnow", description="Ručně vytvoří anketu pro příští týden")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def pollnow(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await send_poll(interaction.channel)


# ==== START ====
bot.run(TOKEN)
