import discord
from discord import app_commands
import importlib

# --- Central place for all slash commands ---
def register_commands(bot: discord.Client):
    tree = bot.tree

    @tree.command(name="run", description="Run platform connection process dynamically")
    @app_commands.describe(platform="Choose a platform (facebook, instagram, linkedin, tiktok)")
    async def run(interaction: discord.Interaction, platform: str):
        platform = platform.lower()
        supported = ["facebook", "instagram", "linkedin", "tiktok"]

        if platform not in supported:
            await interaction.response.send_message(
                f"❌ Unsupported platform. Choose from: {', '.join(supported)}",
                ephemeral=True
            )
            return

        try:
            # Try to import the right service module dynamically
            module = importlib.import_module(f"src.services.{platform}_service")

            # Get the 'connect' function from that module
            connect_func = getattr(module, "connect", None)
            if not connect_func:
                await interaction.response.send_message(
                    f"⚠️ `{platform}_service.py` has no `connect()` function.",
                    ephemeral=True
                )
                return

            # Run the function — supports both sync and async versions
            if callable(connect_func):
                if callable(getattr(connect_func, "__await__", None)):
                    result = await connect_func(interaction.user.id)
                else:
                    result = connect_func(interaction.user.id)
            else:
                result = None

            # Handle returned result
            if isinstance(result, str) and result.startswith("http"):
                await interaction.response.send_message(
                    f"🔗 Click here to connect your **{platform.capitalize()}**:\n{result}",
                    ephemeral=True
                )
            elif result:
                await interaction.response.send_message(
                    f"✅ {platform.capitalize()} connect result:\n{result}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"✅ Ran `{platform}` connect successfully (no output).",
                    ephemeral=True
                )

        except ModuleNotFoundError:
            await interaction.response.send_message(
                f"❌ Service file not found for `{platform}` in `src/services/`.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"💥 Error running `{platform}` connect: {e}",
                ephemeral=True
            )

    # Keep your help command for convenience
    @tree.command(name="help", description="Show all available commands")
    async def help_command(interaction: discord.Interaction):
        commands_list = [
            "/run <platform> — Start a connection or process for that platform",
        ]
        await interaction.response.send_message(
            "**Available commands:**\n" + "\n".join(commands_list),
            ephemeral=True
        )

    print("✅ /run command registered successfully.")
