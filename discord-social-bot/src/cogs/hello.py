from discord.ext import commands

class HelloCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello")
    async def say_hello(self, ctx):
        """Responds with a greeting message."""
        await ctx.send(f"👋 Hello {ctx.author.name}!")

async def setup(bot):
    await bot.add_cog(HelloCog(bot))
