import discord
from discord import app_commands

# --- Central place for all slash commands ---
def register_commands(bot: discord.Client):
    tree = bot.tree

    @tree.command(name="connect", description="Connect your social account")
    @app_commands.describe(platform="Choose a platform to connect")
    async def connect(interaction: discord.Interaction, platform: str):
        platform = platform.lower()
        if platform not in ["facebook", "instagram", "linkedin", "tiktok"]:
            await interaction.response.send_message(
                "❌ Invalid platform. Choose: Facebook, Instagram, LinkedIn, or TikTok.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"🔗 Starting OAuth connection for **{platform.capitalize()}**...",
            ephemeral=True
        )

    @tree.command(name="disconnect", description="Disconnect your social account")
    @app_commands.describe(platform="Choose a platform to disconnect")
    async def disconnect(interaction: discord.Interaction, platform: str):
        await interaction.response.send_message(
            f"🔒 Disconnected your {platform.capitalize()} account.",
            ephemeral=True
        )

    @tree.command(name="page_info", description="Show connected page information")
    async def page_info(interaction: discord.Interaction):
        await interaction.response.send_message("📄 Showing your connected page info...", ephemeral=True)

    @tree.command(name="delete_post", description="Delete a post from a connected platform")
    async def delete_post(interaction: discord.Interaction, platform: str, post_id: str):
        await interaction.response.send_message(
            f"🗑️ Attempting to delete post `{post_id}` from {platform.capitalize()}...",
            ephemeral=True
        )

    @tree.command(name="help", description="Show all available commands")
    async def help_command(interaction: discord.Interaction):
        commands_list = [
            "/connect <platform>",
            "/disconnect <platform>",
            "/page_info",
            "/delete_post <platform> <post_id>",
        ]
        await interaction.response.send_message(
            "**Available commands:**\n" + "\n".join(commands_list),
            ephemeral=True
        )

    print("✅ Commands registered successfully.")
