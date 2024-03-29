from abc import ABC
from logging.handlers import RotatingFileHandler

import discord
import tornado.web
import json
import logging
import tornado.log

from utils.db.cache import BotCache


handler = RotatingFileHandler(filename='logs/tornado.log', maxBytes=1024 * 10, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger = logging.getLogger("tornado.application")
logger.setLevel(logging.ERROR)
logger.addHandler(handler)
tornado.log.enable_pretty_logging(logger=logger)

with open('utils/keys/voting.env') as f:
    token = f.read()


class BaseHandler(tornado.web.RequestHandler, ABC):
    def initialize(self, bot, db):
        self.bot = bot
        self.db = db

    async def prepare(self):
        await self.bot.wait_until_ready()


class TopGGVoteHandler(BaseHandler, ABC):
    async def post(self):
        if self.request.headers.get('Authorization') != token:
            return self.set_status(401)

        data = json.loads(self.request.body)
        if data['bot'] != self.bot.user.id:
            return self.set_status(400)

        user = self.bot.get_user(data['user'])
        if user is not None:
            try:
                embed: discord.Embed = discord.Embed(
                    color=discord.Color.gold(),
                    title='Thank you for voting on TOP.GG <:booster4:703906534534414346>')
                await user.send(embed=embed)
            except discord.Forbidden:
                pass
        self.set_status(200)


class DiscordBotListVoteHandler(BaseHandler, ABC):
    async def post(self):
        if self.request.headers.get('Authorization') != token:
            return self.set_status(401)

        data = json.loads(self.request.body)

        user = self.bot.get_user(data['id'])
        if user is not None:
            try:
                embed: discord.Embed = discord.Embed(
                    color=discord.Color.gold(),
                    title='Thank you for voting on DBL! <:booster4:703906534534414346>')
                await user.send(embed=embed)
            except discord.Forbidden:
                pass
        self.set_status(200)


class CacheUpdater(BaseHandler, ABC):
    async def get(self):
        if not self.request.remote_ip == "127.0.0.1":
            return self.set_status(403)

        update = self.get_arguments("update")
        guild_id = self.get_arguments("guild")

        if not update and not guild_id:
            return self.set_status(400)

        cache: BotCache = self.bot.cache
        guild_cache = await cache.get(int(guild_id[0]))

        if guild_cache:
            if update[0] == "leveling":
                await guild_cache.leveling.reload()
            elif update[0] == "modules":
                await guild_cache.modules.reload()
            elif update[0] == "automod":
                await guild_cache.automod.reload()
            elif update[0] == "config":
                await guild_cache.update_config()
            return self.set_status(200)

        self.set_status(500)


def app(bot, database):
    extras = {
        'bot': bot,
        'db': database
    }
    return tornado.web.Application([
        ('/vote/topgg', TopGGVoteHandler, extras),
        ('/vote/dbl', DiscordBotListVoteHandler, extras),
        ('/update/cache', CacheUpdater, extras)
    ])
