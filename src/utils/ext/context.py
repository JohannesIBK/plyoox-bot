import asyncio
import io

import discord
from discord.ext import commands

from utils.ext import standards


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_pool = self.bot.db
        self._db = None

    async def safe_send(self, content, *, escape_mentions=True, **kwargs):
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        content.replace("`", "")

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop('file', None)
            return await self.send(file=discord.File(fp, filename='message_to_long.txt'), **kwargs)
        else:
            return await self.send(content)

    @property
    def db(self):
        return self._db if self._db else self.db_pool

    async def release(self):
        if self._db is not None:
            await self.bot.pool.release(self._db)
            self._db = None

    async def prompt(self, message, *, timeout=60.0, delete_after=True, reacquire=True, author_id=None):
        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError('Der Bot kann keine Reaktionen hinzufügen.')

        fmt = f'{message}\n\nReagiere mit {standards.yes_emoji} um zu bestätigen oder {standards.no_emoji} um abzubrechen.'

        author_id = author_id or self.author.id
        msg = await self.send(embed=discord.Embed(color=standards.normal_color, description=fmt))

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != msg.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == standards.yes_emoji:
                confirm = True
                return True
            elif codepoint == standards.no_emoji:
                confirm = False
                return True

            return False

        for emoji in (standards.yes_emoji, standards.no_emoji):
            await msg.add_reaction(emoji)

        if reacquire:
            await self.release()

        try:
            await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await msg.delete()
        finally:
            return confirm
