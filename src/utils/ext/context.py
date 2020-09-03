import asyncio
import io

import discord
from asyncpg.pool import Pool
from discord.ext import commands

from utils.ext import standards as std


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db = self.bot.db

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
    def db(self) -> Pool:
        return self._db if self._db else self.bot.db

    async def release(self):
        if self._db is not None:
            await self.bot.pool.release(self._db)
            self._db = None

    async def error(self, message: str, **kwargs):
        await self.send(embed=std.getErrorEmbed(message), **kwargs)

    async def embed(self, message: str, **kwargs):
        await self.send(embed=std.getEmbed(message), **kwargs)

    async def prompt(self, message, *, timeout=60.0, delete_after=True, reacquire=True, author_id=None):
        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError('Der Bot kann keine Reaktionen hinzufügen.')

        fmt = f'{message}\n\nReagiere mit {std.yes_emoji} um zu bestätigen oder {std.no_emoji} um abzubrechen.'

        author_id = author_id or self.author.id
        msg = await self.send(embed=discord.Embed(color=std.normal_color, description=fmt))

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != msg.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == std.yes_emoji:
                confirm = True
                return True
            elif codepoint == std.no_emoji:
                confirm = False
                return True

            return False

        for emoji in (std.yes_emoji, std.no_emoji):
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
