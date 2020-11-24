from logging.handlers import RotatingFileHandler

import discord
import tornado.web
import json
import logging
import tornado.log


handler = RotatingFileHandler(filename='logs/tornado.log', maxBytes=1024 * 10, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger = logging.getLogger("tornado.application")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
tornado.log.enable_pretty_logging(logger=logger)

with open('utils/keys/voting.env') as f:
    token = f.read()


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, bot, db):
        self.bot = bot
        self.db = db

    async def prepare(self):
        await self.bot.wait_until_ready()


class TopGGVoteHandler(BaseHandler):
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
            except:
                pass
        self.set_status(200)


class DiscordBotListVoteHandler(BaseHandler):
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
            except:
                pass
        self.set_status(200)


def app(bot, database):
    extras = {
        'bot': bot,
        'db': database
    }
    return tornado.web.Application([
        ('/vote/topgg', TopGGVoteHandler, extras),
        ('/vote/dbl', DiscordBotListVoteHandler, extras)
    ])