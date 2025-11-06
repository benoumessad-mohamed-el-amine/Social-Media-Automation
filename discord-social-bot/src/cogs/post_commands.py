import discord 
from discord import app_commands
from .base_command import SocialCommandBase
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.model import PublishedPost, PlatformType
from services.facebook import FacebookAPI


class PostCommands(SocialCommandBase):
    @app_commands.command(name="post", description="Post to a platform")
    @app_commands.describe(platform="Social media platform", content="post content")
    @app_commands.choices(platform=[
        app_commands.Choice(name="Facebook", value="facebook"),
        app_commands.Choice(name="Instagram", value="instagram"),
        app_commands.Choice(name="LinkedIn", value="linkedin"),
        app_commands.Choice(name="TikTok", value="tiktok")
    ])
    async def post_command(self, interaction: discord.Interaction, platform: str, content: str):
        await self.execute(interaction, platform=platform, content=content)
    
    
    
    @app_commands.command(name="crosspost", description="Post to all platforms at once")
    @app_commands.describe(content="Content to post")
    async def crosspost_command(self, interaction: discord.Interaction, content: str):
        await self.execute(interaction, content=content, crosspost=True)
        

    
    @app_commands.command(name="post_image", description="Post an image to Facebook")
    @app_commands.describe(image_url="URL of the image to post", account_id="Facebook account ID (optional)")
    async def post_image_command(self, interaction: discord.Interaction, image_url: str, account_id: str = None):
        await self.execute(interaction, image_url=image_url, account_id=account_id, action="post_image")
        
        
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        platform = kwargs.get("platform")
        content = kwargs.get('content')
        crosspost = kwargs.get('crosspost', False)
        image_url = kwargs.get('image_url')
        action = kwargs.get('action')
        account_id = kwargs.get('account_id')
        discord_id = str(interaction.user.id)
        
        
        if action == "post_image":
            await self._post_image(interaction, image_url, account_id, discord_id)
        elif crosspost:
            await self._crosspost(interaction, content, discord_id)
        else:
            await self._post_to_platform(interaction, platform, content, discord_id)
    
    
    
    async def _post_image(self, interaction: discord.Interaction, image_url: str, account_id: str, discord_id: str):
        await self.send_loading(interaction, "Posting image to Facebook.......")
        
        try:
            fb_account = await self.get_facebook_account(account_id)
            if not fb_account:
                await interaction.edit_original_response(content="No active facebook account found")
                return
            
            
            tokens = await self.db.get_tokens(str(fb_account.id))
            if not tokens:
                await interaction.edit_original_response(content="No access token found for this account")
                return
            
            
            fb_api = FacebookAPI(tokens['access_token'])
            result = fb_api.post_image(image_url, fb_account.account_id)
            
            
            if result.get("success"):
                post = PublishedPost(
                    social_account_id=str(fb_account.id),
                    requested_by_discord_id=discord_id,
                    platform=PlatformType.FACEBOOK,
                    content=f"Image post: {image_url}",
                    media_urls=[image_url]
                )
                
                post_id = await self.db.create_published_post(post)
                
                await interaction.edit_original_response(
                    content=f"**Image posted to facebook!**\n"
                        f"**Account:** {fb_account.account_name}\n"
                        f"**Image URL:** {image_url}\n"
                        f"**Post ID:** `{post_id}`"
                )
            
            else:
                await interaction.edit_original_response(content=f"Failed to post image: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            await interaction.edit_original_response(
                content=f"❌ Error posting image: {str(e)}"
            )
        
        
    
    async def _post_to_platform(self, interaction: discord.Interaction, platform: str, content: str, discord_id):
        if platform == "facebook":
            await self._post_to_facebook(interaction, content, discord_id)
        
        else:
            accounts = await self.db.get_all_social_accounts()
            acc = next((a for a in accounts if a.platform.value == platform and a.is_active), None)
            if not acc:
                await self.send_error(interaction, f"No connected {platform} account")
                return
            
            post = PublishedPost(
                social_account_id=str(acc.id),
                requested_by_discord_id=discord_id,
                platform=PlatformType(platform),
                content=content
            )
            post_id = await self.db.create_published_post(post)
            
            
            message = f"Posted to {platform.title()}!\nContent: {content}\nPost ID: `{post_id}`"
            await self.send_success(interaction, message)
    
    
    
    async def _post_to_facebook(self, interaction: discord.Interaction, content: str, discord_id: str):
        await self.send_loading(interaction, "📝 Posting to Facebook...")
        
        try:
            #Get first active Facebook account
            fb_account = await self._get_facebook_account()
            if not fb_account:
                await interaction.edit_original_response(content="❌ No active Facebook account found")
                return
            
            #Get access token
            tokens = await self.db.get_tokens(str(fb_account.id))
            if not tokens:
                await interaction.edit_original_response(content="❌ No access token found for this account")
                return
            
            #Post using Facebook API
            fb_api = FacebookAPI(tokens["access_token"])
            result = fb_api.post_text(content, fb_account.account_id)
            
            if result.get("success"):
                #Store in database
                post = PublishedPost(
                    social_account_id=str(fb_account.id),
                    requested_by_discord_id=discord_id,
                    platform=PlatformType.FACEBOOK,
                    content=content
                )
                post_id = await self.db.create_published_post(post)
                
                await interaction.edit_original_response(
                    content=f"**Posted to Facebook!**\n"
                           f"**Account:** {fb_account.account_name}\n"
                           f"**Content:** {content}\n"
                           f"**Post ID:** `{post_id}`"
                )
            else:
                await interaction.edit_original_response(
                    content=f"Failed to post: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            await interaction.edit_original_response(
                content=f"Error posting to Facebook: {str(e)}"
            )
    
    
    async def _crosspost(self, interaction: discord.Interaction, content: str, discord_id: str):
        await self.send_loading(interaction, "🔄 Cross-posting to all platforms...")
        
        accounts = await self.db.get_all_social_accounts()
        active_accounts = [acc for acc in accounts if acc.is_active]
        
        if not active_accounts:
            await interaction.edit_original_response(content="❌ No active accounts connected for cross-posting.")
            return
        
        results = []
        
        for acc in active_accounts:
            try:
                if acc.platform == PlatformType.FACEBOOK:
                    #Use Facebook API for Facebook posts
                    tokens = await self.db.get_tokens(str(acc.id))
                    if tokens:
                        fb_api = FacebookAPI(tokens["access_token"])
                        result = fb_api.post_text(content, acc.account_id)
                        
                        if result.get("success"):
                            #Store in database
                            post = PublishedPost(
                                social_account_id=str(acc.id),
                                requested_by_discord_id=discord_id,
                                platform=acc.platform,
                                content=content
                            )
                            await self.db.create_published_post(post)
                            results.append(f"- {acc.platform.value.title()}: Posted!")
                        else:
                            results.append(f"- {acc.platform.value.title()}: Failed")
                    else:
                        results.append(f"- {acc.platform.value.title()}: No token")
                else:
                    #For other platforms
                    post = PublishedPost(
                        social_account_id=str(acc.id),
                        requested_by_discord_id=discord_id,
                        platform=acc.platform,
                        content=content
                    )
                    await self.db.create_published_post(post)
                    results.append(f"- {acc.platform.value.title()}: Logged (API not implemented)")
                    
            except Exception as e:
                results.append(f"- {acc.platform.value.title()}: Error: {str(e)}")
        
        message = f"**Cross-posting Results:**\n" + "\n".join(results)
        await interaction.edit_original_response(content=message)
    
    
    
    async def _get_facebook_account(self, specific_account_id: str = None):
        accounts = await self.db.get_all_social_accounts()
        facebook_accounts = [acc for acc in accounts if acc.platform == PlatformType.FACEBOOK and acc.is_active]
        
        if not facebook_accounts:
            return None
        
        if specific_account_id:
            for acc in facebook_accounts:
                if str(acc.id) == specific_account_id or acc.account_id == specific_account_id:
                    return acc
            return None
        
        return facebook_accounts[0] if facebook_accounts else None
    
    
    
    


async def setup(bot):
    await bot.add_cog(PostCommands(bot))
