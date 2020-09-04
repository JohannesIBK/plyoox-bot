# kphoen
# sorin

import asyncio
import argparse

import server
from main import Plyoox as Bot

parser = argparse.ArgumentParser()
parser.add_argument('--prod', type=bool, default=False, required=False)
args = parser.parse_args()

if args.prod:
    with open(r"utils/keys/bot.env") as f:
        token = f.read()
    print("\n\nBot startet...\n")
else:
    with open(r"utils/keys/testbot.env") as f:
        token = f.read()
    print("\n\nStarting Test...\n")


loop = asyncio.get_event_loop()
bot = Bot()

try:
    loop.run_until_complete(bot.create_db_pool())
except:
    print('Es konnte keine Verbindung zu PostgreSQL aufgebaut werden')
    exit()

try:
    loop.run_until_complete(bot.create_redis_pool())
except:
    print('Es konnte keine Verbindung zu RedisDB aufgebaut werden')
    exit()


try:
    web = server.app(bot, bot.db)
    web.listen(8888)
    asyncio.ensure_future(bot.start(token))
except KeyboardInterrupt:
    loop.run_until_complete(bot.logout())
    print('Bot disconnected')

loop.run_forever()
