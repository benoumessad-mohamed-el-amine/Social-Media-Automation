import discord
from discord import app_commands
from base_command import SocialCommandBase


class HelpCommands(SocialCommandBase):
    @app_commands.command(name='help', description='Show all available commands')
    async def help_command(self, interaction: discord.Interaction):
        await self.execute(interaction)
        
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        commands = await self.db.get_all_bot_commands()
    
        if not commands:
             await self.send_error(interaction, "No bot commands found in database.")
             return
    
        message = "**Available Commands:**\n" + "\n".join(
            f"- `/{cmd.name}`: {cmd.description}" for cmd in commands
         )
        await self.send_success(interaction, message)




async def setup(bot):
    await bot.add_cog(HelpCommands(bot))