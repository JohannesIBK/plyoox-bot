import asyncio
import sys

from main import Plyoox as Bot


def close():
    try:
        loop.close()
        exit()
    except:
        exit(1)


if sys.platform == "win32":
    with open(r"others/keys/testbot.env") as f:
        token = f.read()
    print("\n\nStarting Test...\n")
else:
    with open(r"others/keys/bot.env") as f:
        token = f.read()
    print("\n\nBot startet...\n")


loop = asyncio.get_event_loop()
bot = Bot()

try:
    loop.run_until_complete(bot.create_db_pool())
except:
    print('Es konnte keine Verbindung zu PostgreSQL aufgebaut werden')
    close()

try:
    loop.run_until_complete(bot.create_redis_pool())
except:
    print('Es konnte keine Verbindung zu RedisDB aufgebaut werden')
    loop.close()
    close()


async def run_bot():
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    finally:
        await bot.db.close()
        print('Bot disconnected')


loop.run_until_complete(run_bot())
