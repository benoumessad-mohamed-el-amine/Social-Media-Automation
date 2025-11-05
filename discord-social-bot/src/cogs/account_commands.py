import discord
from discord import app_commands
from .base_command import SocialCommandBase



class AccountCommands(SocialCommandBase):
    @app_commands.command(name="accounts", description="List all connected SM accounts")
    async def accounts_command(self, interaction: discord.Interaction):
        await self.execute(interaction)
        
        
    async def execute(self, interaction: discord.Interaction, **kwargs):
        accounts = await self.db.get_all_social_accounts()
    
        if not accounts:
           await self.send_error(interaction, "No connected accounts. Use /connect to add one.")
           return
    
        message = "**Connected Accounts:**\n" + "\n".join(
            f"- {acc.platform.value.title()}: {acc.account_name} (`{acc.account_id or acc.id}`)"
            for acc in accounts
            )
    
        await self.send_success(interaction, message)

            

async def setup(bot):
    await bot.add_cog(AccountCommands(bot))