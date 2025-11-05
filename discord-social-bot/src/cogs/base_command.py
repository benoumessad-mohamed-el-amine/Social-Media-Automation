import discord
from discord.ext import commands
#from .temp.mock_data_provider import MockDataProvider
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.mongodb_handler import db_handler


#test123
class SocialCommandBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #Temporary
        #self.mock_data = MockDataProvider()
        self.db = db_handler
    
    
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        pass
    
    
    async def send_success(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)
    
    
    async def send_error(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)
        
    
    async def send_loading(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)