import io
from datetime import datetime

import discord
from discord.ext import commands

from utils.ext import checks, standards


class Botting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @checks.hasPerms(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @massban.command()
    @commands.bot_has_permissions(ban_members=True)
    async def msg(self, ctx, *, Message):
        lang = await self.bot.lang(ctx)

        banned = []
        count = 0
        async for msg in ctx.channel.history(limit=200):
            if msg.content == Message:
                if (datetime.now() - msg.author.joined_at).days == 0:
                    await msg.author.ban(reason="Botting", delete_message_days=1)
                    count += 1
                    banned.append((count, msg.author, msg.author.id))

        await ctx.send(lang["ban"].format(count=count))

        if len(banned) != 0:
            message = "\n".join(f'{count}. {author} [{author_id}]' for count, author, author_id in banned)
            fp = io.BytesIO(message.encode())
            await ctx.send(file=discord.File(fp, filename='banned_member.txt'))

    @massban.command()
    @commands.bot_has_permissions(ban_members=True)
    async def name(self, ctx, User: discord.Member, nick: bool = False):
        lang = await self.bot.lang(ctx)

        if nick:
            try:
                # noinspection PyUnusedLocal
                u_name = User.nick
            except:
                return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                          description=["error_not_nicked"]))
        else:
            u_name = User.name

            banned = []
            count = 0

            async for msg in ctx.channel.history(limit=200):
                try:
                    if msg.author.nick == u_name:
                        if not (datetime.now() - msg.author.joined_at).days == 0:
                            await msg.author.ban(reason="Botting", delete_message_days=1)
                            count += 1
                            banned.append((count, msg.author, msg.author.id))
                except:
                    pass

            await ctx.send(lang["ban"].format(count=count))

            if len(banned) != 0:
                message = "\n".join(f'{count}. {author} [{author_id}]' for count, author, author_id in banned)
                fp = io.BytesIO(message.encode())
                await ctx.send(file=discord.File(fp, filename='banned_member.txt'))

    @massban.command()
    @commands.bot_has_permissions(ban_members=True)
    async def all(self, ctx, User: discord.Member, nick: bool = False):
        lang = await self.bot.lang(ctx)

        if nick:
            try:
                u_name = User.nick
            except:
                return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                          description=["error_not_nicked"]))
        else:
            u_name = User.name

        banned = []
        count = 0
        members = list(filter(lambda m: m.nick == u_name, ctx.guild.members))
        for member in members:
            await member.ban(reason="Botting", delete_message_days=1)
            count += 1
            banned.append((count, member))

        await ctx.send(lang["ban"].format(count=count))

        if len(banned) != 0:
            message = "\n".join(f'{count}. {author} [{author_id}]' for count, author, author_id in banned)
            fp = io.BytesIO(message.encode())
            await ctx.send(file=discord.File(fp, filename='banned_member.txt'))


def setup(bot):
    bot.add_cog(Botting(bot))
