import discord 
from discord import app_commands
from base_command import SocialCommandBase
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.model import PlatformType

class ModerationCommands(SocialCommandBase):
    @app_commands.command(name="reply", description="Reply to a post comment")
    @app_commands.describe(platform="Social media platform", post_id="ID of the post to reply to", comment="Reply comment content")
    async def reply_command(self, interaction: discord.Interaction, platform: str, post_id: str, comment: str):
        await self.execute(interaction, platform=platform, post_id=post_id, comment=comment)
        
    @app_commands.command(name="delete", description="Delete a post")
    @app_commands.describe(platform="Social media platform", post_id="ID of the post to delete")
    async def delete_command(self, interaction: discord.Interaction, platform: str, post_id: str):
        await self.execute(interaction, platform=platform, post_id=post_id)
    
    async def execute(self, interaction: discord.Interaction, **kwargs):
        platform = kwargs.get('platform')
        post_id = kwargs.get('post_id')
        comment = kwargs.get('comment')
        discord_id = str(interaction.user.id)

        if comment:  # Reply
            # -------------------- TODO: ici appeler le vrai service pour répondre sur le réseau --------------------
            await self.db.log_reply_action(
                platform=PlatformType(platform),
                post_id=post_id,
                comment=comment,
                replied_by_discord_id=discord_id
            )
            await self.send_success(interaction, f"Replied to {platform.title()} post `{post_id}`:\n{comment}")

        else:  # Delete
            # -------------------- TODO: ici appeler le vrai service pour supprimer le post du réseau --------------------
            result = await self.db.delete_post(
                post_id=post_id,
                deleted_by_discord_id=discord_id,
                platform=PlatformType(platform)
            )
            if result["deleted"]:
                await self.send_success(interaction, f"Deleted {platform.title()} post `{post_id}` successfully.")
            else:
                await self.send_error(interaction, f"Failed to delete {platform.title()} post `{post_id}`.")

            


async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))