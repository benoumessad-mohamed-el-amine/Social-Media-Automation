from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Load cogs
bot.load_extension('cogs.hello')

# Run the bot with the token from the config
if __name__ == '__main__':
    import config
    bot.run(config.DISCORD_TOKEN)