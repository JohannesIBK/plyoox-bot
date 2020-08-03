import dbl
from discord.ext import commands

import main


class BotLists(commands.Cog):
    with open(r"./others/keys/dbl.env", 'r') as file:
        dblToken = file.read()

    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.dblpy = dbl.DBLClient(self.bot, self.dblToken, autopost=True)

    async def on_guild_post(self):
        self.bot.logger.info('Posted Server Count')

def setup(bot):
    bot.add_cog(BotLists(bot))