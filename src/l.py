import asyncio
import argparse
import logging
import contextlib
import uvloop
import warnings
from logging.handlers import RotatingFileHandler

import server
from main import Plyoox as Bot


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

warnings.filterwarnings("ignore", category=DeprecationWarning)


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record):
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        max_bytes = 32 * 1024 * 1024
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(filename='logs/discord.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


parser = argparse.ArgumentParser()
parser.add_argument('--prod', type=bool, default=False, required=False)
args = parser.parse_args()

if args.prod:
    with open(r"utils/keys/bot.env") as f:
        port = 5432
        token = f.read()
    print("\n\nBot startet...\n")
else:
    with open(r"utils/keys/testbot.env") as f:
        port = 15432
        token = f.read()
    print("\n\nStarting Test...\n")


def run_bot():
    with setup_logging():
        log = logging.getLogger()
        loop = asyncio.get_event_loop()
        bot = Bot()

        try:
            loop.run_until_complete(bot.create_db_pool(port))
        except Exception:
            print('Es konnte keine Verbindung zu PostgreSQL aufgebaut werden...')
            log.error("Could not connect to Postgres.")
            return

        try:
            web = server.app(bot, bot.db)
            web.listen(8888)
            asyncio.ensure_future(bot.start(token))
        except KeyboardInterrupt:
            loop.run_until_complete(bot.logout())
            print('Bot disconnected')

        loop.run_forever()


run_bot()
