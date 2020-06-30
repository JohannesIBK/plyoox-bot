from discord.ext import commands
from discord.ext import tasks
import main


class Loader(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.loader.start()

    # noinspection PyCallingNonCallable
    @tasks.loop(seconds=1, count=1)
    async def loader(self):
        await self.bot.wait_until_ready()

        cogs = [
            "cogs.Owner",
            "cogs.Moderation",
            "cogs.Servermoderation",
            "cogs.Help",
            "cogs.Leveling",
            "cogs.Utilities",
            "cogs.Commands",
            # "cogs.Errors",
            "cogs.Fun",
            "cogs.Private",
            "cogs.Events",
            "cogs.Infos"
        ]

        for cog in cogs:
            try:
                self.bot.load_extension(cog)
            except commands.ExtensionAlreadyLoaded:
                self.bot.reload_extension(cog)

        for cmd in self.bot.commands:
            self.bot.get_all_commands.update({cmd.name.lower(): cmd})
            for alias in cmd.aliases:
                self.bot.get_all_commands.update({alias.lower(): cmd})

        print(f'{len(cogs)} Cogs loaded.')

    @loader.before_loop
    async def before_loader(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Loader(bot))
