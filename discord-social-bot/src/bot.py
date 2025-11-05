import os
import sys
import logging
import asyncio
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from commands_handler import register_commands  # ✅ fix: correct file name

# Add parent dir to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import internal modules
from services.schedular_service import scheduler_service
from utils.database.mongodb_handler import db_handler

# ─────────────────────────────────────────────
# Logging configuration
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SocialMediaBot")

# ─────────────────────────────────────────────
# Bot setup
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ─────────────────────────────────────────────
# Event handlers
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as: {bot.user} (ID: {bot.user.id})")
    logger.info(f"🌍 Connected to {len(bot.guilds)} guild(s)")

    # ✅ Register all slash commands (from commands_handler)
    register_commands(bot)

    # ✅ Start scheduler (only once)
    loop = asyncio.get_running_loop()
    scheduler_service.scheduler.configure(event_loop=loop)
    scheduler_service.start(db_handler_instance=db_handler)
    logger.info("✅ Scheduler started successfully.")

    # ✅ Sync all slash commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} command(s) with Discord.")
    except Exception as sync_error:
        logger.error(f"❌ Error syncing commands: {sync_error}")

# ─────────────────────────────────────────────
# Simple slash commands
# ─────────────────────────────────────────────
@bot.tree.command(name="hello", description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"👋 Hello, {interaction.user.display_name}!")

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! {latency}ms")

# ─────────────────────────────────────────────
# Bot startup
# ─────────────────────────────────────────────
async def main():
    """Main entry point of the bot"""
    # Connect to MongoDB first
    try:
        await db_handler.connect()
        logger.info("✅ Connected to MongoDB")
    except Exception as db_error:
        logger.error(f"❌ Failed to connect to MongoDB: {db_error}")

    # Start bot
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("❌ DISCORD_TOKEN not found in environment variables.")
        return

    await bot.start(token)

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 Starting Social Media Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually.")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
