import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from server import run_web_server, keep_alive
import threading
import sys
from utils.database.mongodb_handler import db_handler


current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)



load_dotenv()



intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)




@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online!')
    bot.loop.create_task(keep_alive())
    print(f'📊 Connected to {len(bot.guilds)} server(s)')
    
    synced = await bot.tree.sync()
    print(f"✅ Synced {len(synced)} command(s)")
    for cmd in synced:
        print(f"  - {cmd.name}")
        
    print('------')





@bot.event
async def setup_hook():
    try:
        await bot.load_extension('cogs.account_commands')
        await bot.load_extension('cogs.post_commands')
        await bot.load_extension('cogs.moderation_commands')
        await bot.load_extension('cogs.help_commands')
        
        print("All cogs loaded successfully!")
        
        await db_handler.connect()
        print("📡 MongoDB connecté")
    except Exception as e:
        print(f"Error loading cogs: {e}")
        
        
        
@bot.event
async def on_connect():
    
    await bot.tree.sync()
    print("DEBUG: All slash commands synced")






web_thread = threading.Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()



@bot.tree.command(name="test", description="Test if commands work")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Bot commands are working!")
    
@bot.tree.command(name="party", description="say PARTY PARTY YEAH")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(" 🥳 PARTY PARTY YEAH")


if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("DISCORD_TOKEN not found in .env file")
