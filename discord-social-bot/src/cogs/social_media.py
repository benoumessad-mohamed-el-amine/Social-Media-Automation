import discord
from discord.ext import commands
from src.utils.database.mongodb_handler import db_handler
from src.utils.database.model import PlatformType
from src.services import facebook, instagram, linkedin, tiktok


class SocialConnectCog(commands.Cog):
    """Handles social media connection and disconnection."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="connect")
    async def connect_account(self, ctx, platform: str):
        """Connect your social media account."""
        user = await db_handler.get_or_create_user(str(ctx.author.id), ctx.author.name)
        platform = platform.lower()

        if platform not in [p.value for p in PlatformType]:
            await ctx.send("❌ Unsupported platform. Use one of: facebook, instagram, linkedin, tiktok")
            return

        oauth_url = f"https://your-backend-domain.com/oauth/{platform}/authorize?discord_id={ctx.author.id}"
        await ctx.send(f"🔗 Click here to connect your {platform.capitalize()} account:\n{oauth_url}")

        await db_handler.log_command(str(ctx.author.id), "connect", {"platform": platform})

    @commands.command(name="disconnect")
    async def disconnect_account(self, ctx, platform: str):
        """Disconnect your social media account."""
        accounts = await db_handler.get_all_social_accounts()
        account = next((a for a in accounts if a.platform.value == platform.lower()), None)

        if not account:
            await ctx.send(f"❌ No connected {platform} account found.")
            return

        await db_handler.db.social_accounts.delete_one({"_id": account.id})
        await ctx.send(f"🧹 {platform.capitalize()} account disconnected.")
        await db_handler.log_command(str(ctx.author.id), "disconnect", {"platform": platform})


async def setup(bot):
    await bot.add_cog(SocialConnectCog(bot))
