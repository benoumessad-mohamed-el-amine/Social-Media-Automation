import discord
from discord import app_commands
from base_command import SocialCommandBase
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.model import PublishedPost, PlatformType


class PostCommands(SocialCommandBase):
    @app_commands.command(name="post", description="Post to a platform")
    @app_commands.describe(platform="Social media platform", content="Post content")
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
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        platform = kwargs.get('platform')
        content = kwargs.get('content')
        crosspost = kwargs.get('crosspost', False)
        discord_id = str(interaction.user.id)

        if crosspost:
            # Récupérer tous les comptes actifs depuis la DB
            accounts = await self.db.get_all_social_accounts()
            if not accounts:
                await self.send_error(interaction, "No accounts connected for cross-posting.")
                return
            
            posted_platforms = []
            for acc in accounts:
                # TODO: ici, appeler le vrai service pour publier sur le réseau acc.platform
                post = PublishedPost(
                    social_account_id=str(acc.id),
                    requested_by_discord_id=discord_id,
                    platform=acc.platform,
                    content=content
                )
                await self.db.create_published_post(post)
                posted_platforms.append(acc.platform.value.title())
            
            message = f"Cross-posted to {len(posted_platforms)} platforms:\n" + "\n".join(f"- {p}" for p in posted_platforms)
            await self.send_success(interaction, message)

        else:
            # Récupérer le compte pour la plateforme spécifique
            accounts = await self.db.get_all_social_accounts()
            acc = next((a for a in accounts if a.platform.value == platform), None)
            if not acc:
                await self.send_error(interaction, f"No connected {platform} account.")
                return
            
            # TODO: ici, appeler le vrai service pour publier sur le réseau acc.platform
            post = PublishedPost(
                social_account_id=str(acc.id),
                requested_by_discord_id=discord_id,
                platform=PlatformType(platform),
                content=content
            )
            post_id = await self.db.create_published_post(post)

            message = f"Posted to {platform.title()}!\nContent: {content}\nPost ID: `{post_id}`"
            await self.send_success(interaction, message)


async def setup(bot):
    await bot.add_cog(PostCommands(bot))
