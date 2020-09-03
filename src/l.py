# kphoen

import asyncio
import os.path

import server
from main import Plyoox as Bot

if os.path.isfile('test.txt'):
    with open(r"utils/keys/testbot.env") as f:
        token = f.read()
    print("\n\nStarting Test...\n")
else:
    with open(r"utils/keys/bot.env") as f:
        token = f.read()
    print("\n\nBot startet...\n")


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
