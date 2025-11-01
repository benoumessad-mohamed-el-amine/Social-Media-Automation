from discord.ext import commands

class HelloCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """Simple hello command"""
        await ctx.send("Hello, I'm your social media bot!")

async def setup(bot):
    await bot.add_cog(HelloCog(bot))