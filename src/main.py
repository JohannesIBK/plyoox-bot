import asyncio
import json
import logging
import time

import aiohttp
import asyncpg
import discord
from asyncpg.pool import Pool
from discord.ext import commands

from utils.db.cache import BotCache
from utils.ext.context import Context

logger = logging.getLogger(__name__)

with open("utils/languages/de/commands_de.json", 'r') as f:
    lang = dict(json.load(f))

cogs = [
    "plugins.Owner",
    "plugins.Moderation",
    "plugins.Administration",
    "plugins.Help",
    "plugins.Leveling",
    "plugins.Utilities",
    "plugins.Commands",
    "plugins.Errors",
    "plugins.Fun",
    "plugins.Events",
    "plugins.Infos",
    "plugins.Logging",
    "plugins.Timers",
    'plugins.SupportServer'
]

intents = discord.Intents.none()
intents.guild_messages = True
intents.bans = True
intents.presences = True
intents.reactions = True
intents.guilds = True
intents.members = True

intents.invites = False
intents.typing = False
intents.dm_messages = False
intents.emojis = False
intents.voice_states = False
intents.integrations = False


async def getPrefix(bot, msg: discord.Message):
    config = await bot.cache.get(msg.guild.id)
    if config is not None:
        return config.prefix

    return [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']


async def setGame(bot):
    while True:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='plyoox.net | +help'),
            status=discord.Status.online)
        await asyncio.sleep(3600)


class Plyoox(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=getPrefix,
            case_insensitive=True,
            max_messages=10000,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            intents=intents
        )

        self.startTime = time.time()
        self.version = 'v2.7.0'
        self.owner_id = 263347878150406144
        self.commandsCount = {}
        self.cache: BotCache = BotCache(self)
        self._lang = lang

    async def on_ready(self):
        self.gamesLoop = asyncio.create_task(setGame(self))
        self.session = aiohttp.ClientSession(loop=self.loop)

        for cog in cogs:
            try:
                self.load_extension(cog)
            except commands.ExtensionAlreadyLoaded:
                self.reload_extension(cog)

        if self.user.id == 505433541916622850:
            self.load_extension('plugins.BotLists')

        logger.info(time.strftime("Started at %d.%m.%Y %H:%M:%S"))
        logger.info(f"Boot-Time: {round(time.time() - self.startTime, 2)}s")
        logger.info(f'{len(cogs)} Plugins loaded.')
        print(f"Boot-Time: {round(time.time() - self.startTime, 2)}s")
        print(f'Server: {len(self.guilds)} [{self.shard_count}]')
        print(f'{len(cogs)} Plugins loaded.')

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return
        try:
            await self.invoke(ctx)
        finally:
            await ctx.release()

    async def on_command(self, ctx):
        command = ctx.command.parent or ctx.command
        commandName = command.name.lower()

        if commandName not in self.commandsCount:
            self.commandsCount[commandName] = 1
        else:
            self.commandsCount[commandName] += 1

    async def lang(self, guild_id, modul, utils=False):
        if utils:
            return {**self._lang[modul.lower()], **self._lang["utils"]}
        else:
            return self._lang[modul.lower()]

    async def create_db_pool(self, port):
        self.db: Pool = await asyncpg.create_pool(database='discord', user='plyoox', password='1', port=port)

    # async def on_error(self, event_method, *args, **kwargs):
    #      logger.error(traceback.format_exc())
