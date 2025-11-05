import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# --------------------------------------------------
# Configure logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("SocialMediaBot")

# --------------------------------------------------
# Configure Discord bot
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------------------------------------
# Auto-load all cogs from src/cogs/
# --------------------------------------------------
async def load_cogs(bot):
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    if not os.path.exists(cogs_dir):
        logger.warning("⚠️ No 'cogs' directory found. Skipping...")
        return
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = f"src.cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                logger.info(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog_name}: {e}")

# --------------------------------------------------
# Slash Commands (Integrated)
# --------------------------------------------------
@bot.tree.command(name="connect", description="Connect your social media account")
@app_commands.describe(platform="Choose a platform (facebook, instagram, linkedin, tiktok)")
async def connect(interaction: discord.Interaction, platform: str):
    platform = platform.lower()
    if platform not in ["facebook", "instagram", "linkedin", "tiktok"]:
        await interaction.response.send_message(
            "❌ Invalid platform. Choose: Facebook, Instagram, LinkedIn, or TikTok.",
            ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"🔗 Starting OAuth connection for **{platform.capitalize()}**...",
        ephemeral=True
    )

@bot.tree.command(name="disconnect", description="Disconnect a connected social account")
@app_commands.describe(platform="Choose a platform to disconnect")
async def disconnect(interaction: discord.Interaction, platform: str):
    await interaction.response.send_message(
        f"🔒 Disconnected your **{platform.capitalize()}** account.",
        ephemeral=True
    )

@bot.tree.command(name="page_info", description="Show connected page or profile info")
async def page_info(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📄 Fetching your connected page/profile information...",
        ephemeral=True
    )

@bot.tree.command(name="delete_post", description="Delete a post from a connected platform")
@app_commands.describe(platform="Platform name", post_id="ID of the post to delete")
async def delete_post(interaction: discord.Interaction, platform: str, post_id: str):
    await interaction.response.send_message(
        f"🗑️ Deleting post `{post_id}` from **{platform.capitalize()}**...",
        ephemeral=True
    )

@bot.tree.command(name="help", description="Show available bot commands")
async def help_command(interaction: discord.Interaction):
    commands_list = [
        "/connect <platform> - Connect your social account",
        "/disconnect <platform> - Disconnect an account",
        "/page_info - Show connected page info",
        "/delete_post <platform> <post_id> - Delete a post",
        "/help - Show all commands",
    ]
    await interaction.response.send_message(
        "**📘 Available Commands:**\n" + "\n".join(commands_list),
        ephemeral=True
    )

# --------------------------------------------------
# Events
# --------------------------------------------------
@bot.event
async def on_ready():
    logger.info(f"🤖 Logged in as: {bot.user} (ID: {bot.user.id})")
    logger.info(f"🌍 Connected to {len(bot.guilds)} guild(s)")

    # Try syncing slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} command(s) with Discord.")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

@bot.event
async def setup_hook():
    await load_cogs(bot)

# --------------------------------------------------
# Run the bot
# --------------------------------------------------
def main():
    logger.info("🚀 Starting Social Media Bot...")
    if not TOKEN:
        logger.error("❌ DISCORD_TOKEN is missing in .env file")
        return
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
