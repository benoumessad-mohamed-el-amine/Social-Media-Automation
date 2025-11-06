import discord
from discord import app_commands

from services.facebook import FacebookAPI
from utils.database.model import PlatformType
from .base_command import SocialCommandBase



class AccountCommands(SocialCommandBase):      
    @app_commands.command(name="accounts", description="List all connected SM accounts")
    async def accounts_command(self, interaction: discord.Interaction):
        await self.execute(interaction)
        
    
    @app_commands.command(name="connect", description="Connect a facebook account")
    @app_commands.describe(platform="Social media platform", access_token="Access token for the platform", account_name="Name for this account")
    @app_commands.choices(platform=[
        app_commands.Choice(name="Facebook", value="facebook"),
        app_commands.Choice(name="Instagram", value="instagram"),
        app_commands.Choice(name="LinkedIn", value="linkedin"),
        app_commands.Choice(name="TikTok", value="tiktok")
    ])
    async def connect(self, interaction: discord.Interaction, platform: str, access_token: str, account_name: str):
        await self.execute(interaction, platform=platform, access_token=access_token, account_name=account_name, action="connect")
        
    
    
    @app_commands.command(name="disconnect", description="Disconnect a social media account")
    @app_commands.describe(platform="Platform to disconnect from", account_id="Account ID to disconnect")
    @app_commands.choices(platform=[
        app_commands.Choice(name="Facebook", value="facebook"),
        app_commands.Choice(name="Instagram", value="instagram"),
        app_commands.Choice(name="LinkedIn", value="linkedin"),
        app_commands.Choice(name="TikTok", value="tiktok")
    ])
    async def disconnect_account(self, interaction: discord.Interaction, platform: str, account_id: str):
        await self.execute(interaction, platform=platform, account_id=account_id, action="disconnect")
        
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        action = kwargs.get('action')
        platform = kwargs.get('platform')
        
        if action == "connect":
            if platform == "facebook":
                await self._connect_facebook(interaction, kwargs['access_token'], kwargs['account_name'])
            else:
                await self.send_loading(interaction, f"Connecting to {platform.title()}...")
                await self.send_success(interaction, f"Connected to {platform.title()} account: {kwargs['account_name']}")
        
        elif action == "disconnect":
            await self._disconnect_account(interaction, **kwargs)
        else:
            await self._list_accounts(interaction)
       
        
    async def _connect_facebook(self, interaction: discord.Interaction, access_token: str, account_name: str):
        await self.send_loading(interaction, "Connecting to Facebook...")
        
        try:
            
            fb_api = FacebookAPI(access_token)
            result = fb_api.get_page_info()
            print("RESULT\n", result)
            
            if not result.get("success"):
                await interaction.edit_original_response(content=f"Failed to connect: {result.get('error', 'Unknown error')}")
                return
            
            page_data = result.get("data", {})
            page_id = page_data.get("id")
            page_name = page_data.get("name", account_name)
            
            pages = await self._get_user_pages(interaction, access_token)
            
            if not pages:
                await interaction.edit_original_response(content="Failed to get your Facebook pages")
                return
            
            page_access_token = None
            
            for page in pages:
                if page.get("id") == page_id:
                    page_access_token = page.get('access_token')
                    break
            
            if not page_access_token:
                await interaction.edit_original_response(content="Could not retrieve page access token")
                return
            
            #--------------------------db
            account_id = await self.db.add_social_account(
                platform=PlatformType.FACEBOOK,
                account_name=page_name,
                access_token=page_access_token,
                account_id=page_id
            )
            
            await self.db.log_activity(
                discord_id=str(interaction.user.id),
                bot_command_id="connect",
                social_account_id=account_id,
                details={"action": "facebook_connect", "page_name": page_name}
            )
            
            await interaction.edit_original_response(
                content=f"**Facebook Account Connected!**\n"
                    f"**Page:** {page_name}\n"
                    f"**Page ID:** `{page_id}`\n"
                    f"**Database ID:** `{account_id}`"
            )
            
            return page_access_token
            
        except Exception as e:
            await interaction.edit_original_response(
                content=f"Error connecting to Facebook: {str(e)}"
            )
        
    
    
    async def _disconnect_account(self, interaction: discord.Interaction, platform: str, account_id: str):
        await self.send_loading(interaction, "🔌 Disconnecting account...")
        
        try:
            accounts = await self.db.get_all_social_accounts()
            account_to_disconnect = None
            
            for account in accounts:
                if (account.platform.value == platform and 
                    (str(account.id) == account_id or account.account_id == account_id)):
                    account_to_disconnect = account
                    break
            
            if not account_to_disconnect:
                await interaction.edit_original_response(
                    content=f"Account not found for {platform} with ID: {account_id}"
                )
                return
            
            #------------------DB
            #Mark as INACTIVE in database
            await self.db.db.social_accounts.update_one(
                {"_id": account_to_disconnect.id},
                {"$set": {"is_active": False}}
            )
            
            await self.db.log_activity(
                discord_id=str(interaction.user.id),
                bot_command_id="disconnect",
                social_account_id=str(account_to_disconnect.id),
                details={"action": "account_disconnect", "platform": platform}
            )
            
            await interaction.edit_original_response(
                content=f"**Account Disconnected!**\n"
                       f"**Platform:** {platform.title()}\n"
                       f"**Account:** {account_to_disconnect.account_name}\n"
                       f"**ID:** `{account_to_disconnect.account_id}`"
            )
            
        except Exception as e:
            await interaction.edit_original_response(
                content=f"Error disconnecting account: {str(e)}"
            )
      
      
      
    
    async def _list_accounts(self, interaction: discord.Interaction):
        accounts = await self.db.get_all_social_accounts()
        
        if not accounts:
            await self.send_error(interaction, "No connected accounts, use `/connect` to add one")
            return
        
        active_accounts = [acc for acc in accounts if acc.is_active]
        inactive_accounts = [acc for acc in accounts if not acc.is_active]
        
        message_parts = []
        
        if active_accounts:
            message_parts.append("**Connected Accounts:**")
            for acc in active_accounts:
                status = "ACTIVE"
                message_parts.append(
                    f"- {acc.platform.value.title()}: {acc.account_name} "
                    f"(ID: `{acc.account_id or acc.id}`) {status}"
                )
        
        if inactive_accounts:
            message_parts.append("\n**Disconnected Accounts:**")
            for acc in inactive_accounts:
                message_parts.append(
                    f"- {acc.platform.value.title()}: {acc.account_name} "
                    f"(ID: `{acc.account_id or acc.id}`)"
                )
        
        message = "\n".join(message_parts)
        await self.send_success(interaction, message)

      
      
    async def _get_user_pages(self, access_token: str):
        try:
            fb_api = FacebookAPI(access_token)
            result = fb_api._make_request("GET", "me/accounts")
            
            if not result.get("success"):
                return None
            
            pages_data = result.get("data", {}).get("data", [])
            return pages_data
        except Exception as e:
            return None
        
      
      


async def setup(bot):
    await bot.add_cog(AccountCommands(bot))
