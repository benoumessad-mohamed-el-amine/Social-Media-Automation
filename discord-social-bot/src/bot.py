import os
from dotenv import load_dotenv
from discord.ext import commands

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def setup_hook():
    # Load your HelloCog
    await bot.load_extension("src.cogs.hello")

bot.setup_hook = setup_hook

# Run the bot
bot.run(TOKEN)
