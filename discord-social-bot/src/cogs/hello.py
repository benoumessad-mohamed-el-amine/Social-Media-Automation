from discord.ext import commands

class HelloCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send('Hello, World!')

def setup(bot):
    bot.add_cog(HelloCog(bot))