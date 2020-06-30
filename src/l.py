import asyncio

from main import Plyoox as Bot
import sys


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
    loop.run_until_complete(bot.start(token))
except KeyboardInterrupt:
    loop.run_until_complete(bot.logout())
finally:
    loop.close()
