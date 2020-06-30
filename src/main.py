import asyncio
import json
import logging
import random
import traceback

import time
from logging.handlers import RotatingFileHandler

import aiohttp
import aioredis
import asyncpg
import discord
from discord.ext import commands

from others import db
from utils.ext import context

# ---------------------------------------------------------------
handler = RotatingFileHandler(filename='discord.log', maxBytes=1024 * 10, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
logger.addHandler(handler)


# ---------------------------------------------------------------


async def getPrefix(bot, msg: discord.Message):
    userID = bot.user.id

    prefixes = [f'<@!{userID}> ', f'<@{userID}> ']
    if not msg.guild:
        return prefixes
    else:
        prefixes.append(await bot.get(msg.guild.id, 'prefix'))
    return prefixes


async def setGame(bot):
    while True:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='plyoox.net | +help'),
            status=random.choice([discord.Status.idle, discord.Status.dnd, discord.Status.online]))
        await asyncio.sleep(3600)


class Plyoox(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=getPrefix,
                         case_insensitive=True,
                         max_messages=5000)

        self.startTime: float = time.time()
        self.version: str = 'v2.3.0 '
        self.owner_id: int = 263347878150406144
        self.get_all_commands: dict = {}
        self.logger: logging.Logger = logger
        self.remove_command("help")
        self.loop.run_until_complete(self.create_db_pool())
        self.loop.run_until_complete(self.create_redis_pool())

    async def on_ready(self):
        self.gamesLoop = asyncio.create_task(setGame(self))
        self.session = aiohttp.ClientSession(loop=self.loop)

        try:
            self.load_extension("cogs.Loader")
        except commands.ExtensionAlreadyLoaded:
            pass

        logger.info(time.strftime("Started: %d.%m.%Y um %H:%M:%S"))
        print(time.strftime("StartTime: %d.%m.%Y um %H:%M:%S"))
        print(f"Boot-Time: {round(time.time() - self.startTime, 2)}")
        print(f'Server: {len(self.guilds)} [{self.shard_count}]')

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return
        try:
            await self.invoke(ctx)
        finally:
            await ctx.release()

    @staticmethod
    async def on_disconnect():
        logger.info(time.strftime("Disconnected at: %d.%m.%Y um %H:%M:%S"))

    @staticmethod
    async def on_resumed():
        logger.info(time.strftime("Resumed at: %d.%m.%Y um %H:%M:%S"))

    async def get(self, guildID: int, item: str):
        data = await self.redis.get(guildID, encoding='utf-8')
        try:
            returnData = json.loads(data)[item]
            if item in ['noxproles', 'noxpchannels'] and item is not None:
                return list(map(int, returnData))
            return returnData
        except:
            if item == 'prefix':
                query = 'SELECT prefix FROM config.guild WHERE sid = $1'
            elif item in ['noxproles', 'noxpchannels']:
                query = 'SELECT noxproles, noxpchannels FROM config.leveling WHERE sid = $1'
            elif item in ['words', 'state']:
                query = 'SELECT words, state FROM automod.blacklist WHERE sid = $1'
            elif item in ['leveling', 'automod']:
                query = 'SELECT leveling, automod FROM config.modules WHERE sid = $1'
            else:
                raise TypeError(f'Item {item} in DB not found')

            resp = await self.db.fetchrow(query, guildID)

            if resp is None:
                await db.gotAddet(self, self.get_guild(guildID))
                resp = await self.db.fetchrow(query, guildID)

            if data is None:
                await self.redis.set(guildID, json.dumps({item: resp[item]}))
            else:
                currentGuildData = json.loads(await self.redis.get(guildID, encoding='utf-8'))
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

    # async def on_error(self, event_method, *args, **kwargs):
    #     logger.error(traceback.format_exc())
