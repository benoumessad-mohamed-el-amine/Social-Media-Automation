import discord
from discord import app_commands
from base_command import SocialCommandBase
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.model import PlatformType
from utils.oauth import instagram_oauth_handler
from services.instagram import instagram_api
from datetime import datetime


class InstagramCommands(SocialCommandBase):
    def __init__(self, bot):
        super().__init__(bot)

    # -------------------- CONNECT --------------------
    @app_commands.command(name="connect_instagram", description="Connect your Instagram Business account")
    async def connect_instagram(self, interaction: discord.Interaction):
        """Envoie le lien OAuth Instagram à l'utilisateur pour connecter son compte."""
        auth_url = instagram_oauth_handler.get_auth_url(str(interaction.user.id))
        await self.send_success(
            interaction,
            f"🔗 Click below to connect your Instagram account:\n{auth_url}"
        )

    # -------------------- DISCONNECT --------------------
    @app_commands.command(name="disconnect_instagram", description="Disconnect your connected Instagram account")
    async def disconnect_instagram(self, interaction: discord.Interaction):
        """Désactive le compte Instagram lié à ce serveur/utilisateur."""
        accounts = await self.db.get_all_social_accounts()
        instas = [a for a in accounts if a.platform == PlatformType.INSTAGRAM and a.is_active]

        if not instas:
            await self.send_error(interaction, "No active Instagram account found.")
            return

        for acc in instas:
            await self.db.db.social_accounts.update_one(
                {"_id": acc.id},
                {"$set": {"is_active": False}}
            )

        await self.send_success(interaction, "🟠 Instagram account disconnected successfully.")

    # -------------------- POST --------------------
    @app_commands.command(name="post_instagram", description="Post an image or caption to Instagram")
    @app_commands.describe(content="Caption of the post", media_url="Optional image or video URL")
    async def post_instagram(self, interaction: discord.Interaction, content: str, media_url: str = None):
        """Publie un post sur Instagram."""
        await self.send_loading(interaction, "📤 Uploading to Instagram...")

        # Vérifie qu'un compte Instagram est connecté
        accounts = await self.db.get_all_social_accounts()
        insta_acc = next((a for a in accounts if a.platform == PlatformType.INSTAGRAM and a.is_active), None)

        if not insta_acc:
            await self.send_error(interaction, "❌ No connected Instagram account found.")
            return

        # Récupère un token valide
        access_token = await instagram_oauth_handler.get_valid_token(insta_acc.account_id)

        # Appel API pour créer et publier le média
        post_id = await instagram_api.post_media(insta_acc.account_id, content, [media_url] if media_url else None, access_token)

        if post_id:
            await self.send_success(interaction, f"✅ Posted to Instagram successfully!\n**Post ID:** `{post_id}`")
        else:
            await self.send_error(interaction, "❌ Failed to post to Instagram.")

    # -------------------- RECENT POSTS --------------------
    @app_commands.command(name="recent_instagram", description="Fetch your 5 most recent Instagram posts")
    @app_commands.describe(limit="Number of posts to fetch (default 5)")
    async def recent_instagram(self, interaction: discord.Interaction, limit: int = 5):
        """Affiche les posts récents du compte connecté."""
        await self.send_loading(interaction, "📊 Fetching your recent Instagram posts...")

        accounts = await self.db.get_all_social_accounts()
        insta_acc = next((a for a in accounts if a.platform == PlatformType.INSTAGRAM and a.is_active), None)

        if not insta_acc:
            await self.send_error(interaction, "No connected Instagram account found.")
            return

        access_token = await instagram_oauth_handler.get_valid_token(insta_acc.account_id)
        posts = await instagram_api.get_recent_posts(insta_acc.account_id, limit, access_token)

        if not posts:
            await self.send_error(interaction, "No recent posts found.")
            return

        message = "**📰 Recent Instagram Posts:**\n"
        for p in posts:
            caption = (p.get('caption', '')[:50] + '...') if p.get('caption') else 'No caption'
            message += f"- 📸 `{p['id']}` • {p['media_type']} • {caption}\n"

        await self.send_success(interaction, message)

    # -------------------- DELETE --------------------
    @app_commands.command(name="delete_instagram", description="Delete a specific Instagram post by ID")
    @app_commands.describe(post_id="ID of the post to delete")
    async def delete_instagram(self, interaction: discord.Interaction, post_id: str):
        """Supprime un post Instagram."""
        await self.send_loading(interaction, f"🗑️ Deleting Instagram post `{post_id}`...")

        accounts = await self.db.get_all_social_accounts()
        insta_acc = next((a for a in accounts if a.platform == PlatformType.INSTAGRAM and a.is_active), None)

        if not insta_acc:
            await self.send_error(interaction, "No connected Instagram account found.")
            return

        access_token = await instagram_oauth_handler.get_valid_token(insta_acc.account_id)
        success = await instagram_api.delete_post(post_id, insta_acc.account_id, access_token)

        if success:
            await self.send_success(interaction, f"✅ Instagram post `{post_id}` deleted successfully.")
        else:
            await self.send_error(interaction, f"❌ Failed to delete Instagram post `{post_id}`.")

    # -------------------- STATS --------------------
    @app_commands.command(name="stats_instagram", description="Display analytics for your last 10 Instagram posts")
    async def stats_instagram(self, interaction: discord.Interaction):
        """Affiche des statistiques d'engagement pour les 10 derniers posts."""
        await self.send_loading(interaction, "📈 Gathering analytics for your last posts...")

        accounts = await self.db.get_all_social_accounts()
        insta_acc = next((a for a in accounts if a.platform == PlatformType.INSTAGRAM and a.is_active), None)

        if not insta_acc:
            await self.send_error(interaction, "No connected Instagram account found.")
            return

        access_token = await instagram_oauth_handler.get_valid_token(insta_acc.account_id)
        posts = await instagram_api.get_recent_posts(insta_acc.account_id, limit=10, access_token=access_token)

        if not posts:
            await self.send_error(interaction, "No posts found for analytics.")
            return

        message = "**📊 Instagram Analytics (last 10 posts):**\n"
        for p in posts:
            insights = await instagram_api.get_post_insights(p['id'], insta_acc.account_id, access_token)
            message += f"- 🆔 `{p['id']}` • 👍 {insights.get('likes', 0)} • 💬 {insights.get('comments', 0)} • 📈 Engagement: {insights.get('engagement', 0)}\n"

        await self.send_success(interaction, message)


async def setup(bot):
    await bot.add_cog(InstagramCommands(bot))
