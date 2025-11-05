# discordbot.py
import discord
from discord.ext import commands
from discord import app_commands
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import de ton handler MongoDB
from utils.database.mongodb_handler import db_handler
from utils.database.model import PlatformType, PublishedPost


# ----------------------------------------------------------------
# Classe de base (SocialCommandBase)
# ----------------------------------------------------------------
class SocialCommandBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db_handler

    async def send_success(self, interaction, message: str):
        await interaction.response.send_message(f"✅ {message}", ephemeral=True)

    async def send_error(self, interaction, message: str):
        await interaction.response.send_message(f"❌ {message}", ephemeral=True)


# ----------------------------------------------------------------
# Commandes : Accounts, Help, Moderation, Post réunies
# ----------------------------------------------------------------
class SocialCommands(SocialCommandBase):

    # ----- /accounts -----
    @app_commands.command(name="accounts", description="List all connected SM accounts")
    async def accounts_command(self, interaction: discord.Interaction):
        accounts = await self.db.get_all_social_accounts()
        if not accounts:
            await self.send_error(interaction, "No connected accounts. Use /connect to add one.")
            return
        message = "**Connected Accounts:**\n" + "\n".join(
            f"- {a.platform.value.title()}: {a.account_name} (`{a.account_id or a.id}`)" for a in accounts
        )
        await self.send_success(interaction, message)

    # ----- /help -----
    @app_commands.command(name="help", description="Show all available commands")
    async def help_command(self, interaction: discord.Interaction):
        commands = await self.db.get_all_bot_commands()
        if not commands:
            await self.send_error(interaction, "No bot commands found in database.")
            return
        message = "**Available Commands:**\n" + "\n".join(
            f"- `/{cmd.name}`: {cmd.description}" for cmd in commands
        )
        await self.send_success(interaction, message)

    # ----- /reply -----
    @app_commands.command(name="reply", description="Reply to a post comment")
    @app_commands.describe(platform="Social media platform", post_id="ID of the post", comment="Reply content")
    async def reply_command(self, interaction: discord.Interaction, platform: str, post_id: str, comment: str):
        discord_id = str(interaction.user.id)
        await self.db.log_reply_action(
            platform=PlatformType(platform),
            post_id=post_id,
            comment=comment,
            replied_by_discord_id=discord_id
        )
        await self.send_success(interaction, f"Replied to {platform.title()} post `{post_id}`:\n{comment}")

    # ----- /delete -----
    @app_commands.command(name="delete", description="Delete a post")
    @app_commands.describe(platform="Social media platform", post_id="ID of the post")
    async def delete_command(self, interaction: discord.Interaction, platform: str, post_id: str):
        discord_id = str(interaction.user.id)
        result = await self.db.delete_post(
            post_id=post_id,
            deleted_by_discord_id=discord_id,
            platform=PlatformType(platform)
        )
        if result["deleted"]:
            await self.send_success(interaction, f"Deleted {platform.title()} post `{post_id}` successfully.")
        else:
            await self.send_error(interaction, f"Failed to delete {platform.title()} post `{post_id}`.")

    # ----- /post -----
    @app_commands.command(name="post", description="Post to a platform")
    @app_commands.describe(platform="Social media platform", content="Post content")
    @app_commands.choices(platform=[
        app_commands.Choice(name="Facebook", value="facebook"),
        app_commands.Choice(name="Instagram", value="instagram"),
        app_commands.Choice(name="LinkedIn", value="linkedin"),
        app_commands.Choice(name="TikTok", value="tiktok")
    ])
    async def post_command(self, interaction: discord.Interaction, platform: str, content: str):
        discord_id = str(interaction.user.id)

        accounts = await self.db.get_all_social_accounts()
        acc = next((a for a in accounts if a.platform.value == platform), None)
        if not acc:
            await self.send_error(interaction, f"No connected {platform} account.")
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

    # ----- /crosspost -----
    @app_commands.command(name="crosspost", description="Post to all connected platforms")
    @app_commands.describe(content="Content to post on all platforms")
    async def crosspost_command(self, interaction: discord.Interaction, content: str):
        accounts = await self.db.get_all_social_accounts()
        if not accounts:
            await self.send_error(interaction, "No accounts connected for cross-posting.")
            return

        discord_id = str(interaction.user.id)
        posted_platforms = []

        for acc in accounts:
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


# ----------------------------------------------------------------
# Lancement du bot
# ----------------------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté en tant que {bot.user}")


async def setup_hook():
    await db_handler.connect()
    await bot.add_cog(SocialCommands(bot))
    print("📡 MongoDB connecté et commandes chargées.")


bot.setup_hook = setup_hook


# ⚠️ Mets ici ton vrai token Discord :
bot.run("DISCORDTOKEN")
