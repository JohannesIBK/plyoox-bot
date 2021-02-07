import time
import importlib
import io
import json
import operator
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands

import main
from utils.ext import context
from utils.ext.cmds import cmd, grp


class Owner(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    # --------------------------------commands--------------------------------

    @cmd(hidden=True, aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx: context.Context):
        def sort(val):
            return len(val.members)

        count = 0
        msg = f"Total Servers: {len(self.bot.guilds)} | Total Members: {len(list(self.bot.get_all_members()))}\nID | Member | Bots | Name | Owner\n"

        guilds = [guild for guild in self.bot.guilds]
        guilds.sort(key=sort, reverse=True)

        for guild in guilds:
            bots = len([m.bot for m in guild.members if m.bot])
            count += 1
            msg += f"{count}. {guild.id} | {guild.member_count} | {bots} | {guild.name} | {guild.owner}\n"

        await ctx.safe_send(msg, escape_mentions=True)

    @cmd(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: context.Context, cog):
        self.bot.load_extension(cog)
        await ctx.embed(f'Das Modul {cog} wurde geladen.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: context.Context, cog):
        self.bot.reload_extension(cog)
        await ctx.embed(f'Das Modul {cog} wurde neugeladen.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: context.Context, cog):
        self.bot.unload_extension(cog)
        await ctx.embed(f'Das Modul {cog} wurde entladen.')

    @cmd(hidden=True, aliases=['quit'])
    @commands.is_owner()
    async def shutdown(self, ctx: context.Context):
        await ctx.send("Shutdown")
        await self.bot.logout()

    @cmd(name='eval', aliases=["exec"], hidden=True)
    @commands.is_owner()
    async def _eval(self, ctx: context.Context, *, body: str):
        def cleanup_code(content):
            if content.startswith('```') and content.endswith('```'):
                return '\n'.join(content.split('\n')[1:-1])

            return content.strip('` \n')

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
        }

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except discord.Forbidden:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @cmd(hidden=True)
    @commands.is_owner()
    async def logdata(self, ctx: context.Context):
        file = discord.File("discord.log", filename="discord.log")
        await ctx.send(file=file)

    @cmd(hidden=True)
    @commands.is_owner()
    async def setVersion(self, ctx: context.Context, version: str):
        self.bot.version = version
        await ctx.embed(f'Die Version wurde zu {version} geändert.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def sql(self, ctx: context.Context, pg_type: str, *, sql: str):
        if pg_type == 'exec':
            resp = await self.bot.db.execute(sql)
        elif pg_type == 'fetch':
            resp = await self.bot.db.fetch(sql)
        elif pg_type == 'fetchrow':
            resp = await self.bot.db.fetchrow(sql)
        elif pg_type == 'fetchval':
            resp = await self.bot.db.fetchval(sql)
        else:
            return await ctx.error('Keine valider type')

        await ctx.embed(str(resp))

    @cmd(hidden=True)
    @commands.is_owner()
    async def reloadutils(self, ctx: context.Context, name: str):
        try:
            module_name = importlib.import_module(name)
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.error(f"Couldn't find module named **{name}**")

        except Exception as e:
            return await ctx.embed(f'```py\n{e}{traceback.format_exc()}\n```')

        await ctx.send(f"Reloaded module **{name}**")

    @grp(case_insensitive=True, hidden=True)
    @commands.is_owner()
    async def globalban(self, ctx: context.Context):
        pass

    @globalban.command()
    async def add(self, ctx: context.Context, user_id: int, *, reason: str):
        await self.bot.db.execute('INSERT INTO extra.globalbans (userid, reason) VALUES ($1, $2)', user_id, reason)
        await ctx.embed('Der User wurde erfolgreich zur Globalban-Liste hinzugefügt.')

    @globalban.command()
    async def remove(self, ctx: context.Context, user_id: int):
        await self.bot.db.execute('DELETE FROM extra.globalbans WHERE userid = $1', user_id)
        await ctx.embed('Der User wurde erfolgreich von der Globalban-Liste entfernt.')

    @grp(case_insesitive=True, hidden=True)
    @commands.is_owner()
    async def commandCount(self, ctx: context.Context):
        pass

    @commandCount.command()
    async def reverse(self, ctx: context.Context):
        commands_count = self.bot.commandsCount
        commands_count_sorted = sorted(commands_count.items(), key=operator.itemgetter(1))
        commands_count_list = []
        command_range = 15 and len(commands_count_sorted)

        for i in range(command_range):
            command = commands_count_sorted[i]
            commands_count_list.append(f'**{command[0]}:** {command[1]}')

        await ctx.embed('\n'.join(commands_count_list))

    @commandCount.command()
    async def top(self, ctx: context.Context):
        commands_count = self.bot.commandsCount
        commands_count_sorted = sorted(commands_count.items(), key=operator.itemgetter(1))
        commands_count_sorted.reverse()
        commands_count_list = []
        command_range = 15 and len(commands_count_sorted)

        for i in range(command_range):
            command = commands_count_sorted[i]
            commands_count_list.append(f'**{command[0]}:** {command[1]}')

        await ctx.embed('\n'.join(commands_count_list))

    @cmd(hidden=True)
    @commands.is_owner()
    async def loadfrommee6(self, ctx: context.Context):
        if not len(ctx.message.attachments):
            return await ctx.error("Kein Attachment gegeben.")

        attachment = ctx.message.attachments[0]
        data = await attachment.read()
        data = data.decode("utf-8")
        users = json.loads(data)

        for user in users:
            await ctx.db.execute(
                "INSERT INTO extra.levels (uid, sid, xp, time) VALUES ($1, $2, $3, $4) ON CONFLICT (uid, sid) DO UPDATE SET xp = $3",
                user["uid"], ctx.guild.id, user["xp"], time.time()
            )

        await ctx.send("Level gespeichert")


def setup(bot):
    bot.add_cog(Owner(bot))
