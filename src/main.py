import asyncio
import json
import logging
import time
import traceback
from logging.handlers import RotatingFileHandler

import aiohttp
import aioredis
import asyncpg
import discord
from discord.ext import commands

from other import db
from utils.ext import context

# ---------------------------------------------------------------
handler = RotatingFileHandler(filename='logs/discord.log', maxBytes=1024 * 10, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
logger.addHandler(handler)
# ---------------------------------------------------------------

cogs = [
    "plugins.Owner",
    "plugins.Moderation",
    "plugins.Servermoderation",
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


async def getPrefix(bot, msg: discord.Message):
    prefixes = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ']
    if not msg.guild:
        return prefixes
    else:
        prefix = await bot.get(msg.guild.id, 'prefix')
        prefixes.append(prefix)
    return prefixes


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
        super().__init__(command_prefix=getPrefix,
                         case_insensitive=True,
                         max_messages=10000,
                         allowed_mentions=discord.AllowedMentions(everyone=False, roles=False))

        self.startTime: float = time.time()
        self.version: str = 'v2.6.0'
        self.owner_id: int = 263347878150406144
        self.get_all_commands: dict = {}
        self.logger = logger
        self.remove_command("help")
        self.commandsCount = {}

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

        for cmd in self.commands:
            self.get_all_commands.update({cmd.name.lower(): cmd})
            for alias in cmd.aliases:
                self.get_all_commands.update({alias.lower(): cmd})

        logger.info(time.strftime("Started: %d.%m.%Y um %H:%M:%S"))
        print(time.strftime("StartTime: %d.%m.%Y um %H:%M:%S"))
        print(f"Boot-Time: {round(time.time() - self.startTime, 2)}")
        print(f'Server: {len(self.guilds)} [{self.shard_count}]')
        print(f'{len(cogs)} Cogs loaded.')

    async def get_context(self, message, *, cls = context.Context):
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

    async def get(self, guildID: int, item: str):
        data = await self.redis.get(guildID, encoding='utf-8')
        if data is not None:
            try:
                redisData = json.loads(data)[item]
                if item == 'noxpchannels':
                    if redisData is None:
                        return None
                    return list(map(int, redisData))
                elif item == 'noxprole':
                    if redisData is None:
                        return None
                    return int(redisData)
                return redisData
            except KeyError:
                pass

        if item == 'prefix':
            query = 'SELECT prefix FROM config.guild WHERE sid = $1'
        elif item in ['noxprole', 'noxpchannels']:
            query = 'SELECT noxprole, noxpchannels FROM config.leveling WHERE sid = $1'
        elif item in ['words', 'state']:
            query = 'SELECT words, state FROM automod.blacklist WHERE sid = $1'
        elif item in ['leveling', 'automod']:
            query = 'SELECT leveling, automod FROM config.modules WHERE sid = $1'
        else:
            raise ValueError(f'Item {item} in DB not found')

        resp = await self.db.fetchrow(query, guildID)
        if resp is None and item in ['prefix', 'leveling', 'automod']:
            await db.gotAddet(self, self.get_guild(guildID))
            resp = await self.db.fetchrow(query, guildID)
        elif resp is None:
            return None

        if data is None:
            await self.redis.set(guildID, json.dumps({item: resp[item]}))
        else:
            currentGuildData = json.loads(await self.redis.get(guildID, encoding='utf-8'))
            if currentGuildData is None:
                return None
            currentGuildData[item] = resp[item]
            await self.redis.set(guildID, json.dumps(currentGuildData))
        return resp[item]

    async def update_redis(self, guildID, data: dict):
        currentData: dict = json.loads(await self.redis.get(guildID, encoding='utf-8'))
        if currentData is None:
            return await self.redis.get(guildID, "{}")
        currentData.update(data)
        await self.redis.set(guildID, json.dumps(currentData))

    async def create_db_pool(self):
        self.db = await asyncpg.create_pool(database='discord', user='plyoox', password='1')

    async def create_redis_pool(self):
        self.redis = await aioredis.create_redis_pool('redis://localhost/')

    async def on_error(self, event_method, *args, **kwargs):
         logger.error(traceback.format_exc())
