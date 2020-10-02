import codecs
import datetime
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

    @cmd(hidden=True)
    @commands.is_owner()
    async def addRole(self, ctx: context.Context, role: discord.Role):
        count = 0
        members = [member for member in ctx.guild.members if len(member.roles) == 1 and not member.bot]
        for member in members:
            if ctx.me.top_role > member.top_role:
                try:
                    await member.add_roles(role)
                    count += 1
                except discord.Forbidden:
                    break
        await ctx.embed(f'{count} haben den Rang erhalten.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def removeRole(self, ctx: context.Context, role: discord.Role):
        count = 0
        f_count = 0
        for member in role.members:
            try:
                await member.remove_roles(role)
                count += 1
            except discord.Forbidden:
                f_count += 1

        await ctx.embed(f'{count} haben den entzogen bekommen, {f_count} haben den Rang behalten.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def leave(self, ctx: context.Context):
        await ctx.guild.leave()

    @cmd(hidden=True, aliases=['quit'])
    @commands.is_owner()
    async def shutdown(self, ctx: context.Context):
        await ctx.send("Shutdown")
        await self.bot.logout()

    @cmd()
    @commands.is_owner()
    async def permissions(self, ctx: context.Context):
        permissions = ctx.channel.permissions_for(ctx.me)

        embed = discord.Embed(title='Permissions', color=0x3498db)
        embed.add_field(name='Server', value=ctx.guild)
        embed.add_field(name='Channel', value=ctx.channel, inline=False)

        for item, valueBool in permissions:
            if valueBool is True:
                value = ':white_check_mark:'
            else:
                value = ':x:'
            embed.add_field(name=item, value=value)

        embed.timestamp = datetime.datetime.utcnow()
        await self.bot.get_user(263347878150406144).send(embed=embed, delete_after=120)

    @cmd(pass_context=True, name='eval', aliases=["exec"])
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
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @cmd()
    @commands.is_owner()
    async def logdata(self, ctx: context.Context):
        file = discord.File("discord.log", filename="discord.log")
        await ctx.send(file=file)

    @cmd()
    @commands.is_owner()
    async def setVersion(self, ctx: context.Context, version: str):
        self.bot.version = version
        await ctx.embed(f'Die Version wurde zu {version} geändert.')

    @cmd()
    @commands.is_owner()
    async def reloadLang(self, ctx: context.Context):
        self.bot.get_cog('Help').helpText = json.load(codecs.open(r'utils/json/help_de.json', encoding='utf-8'))
        await ctx.embed('Der Help-Text wurde reloadet.')

    @cmd()
    @commands.is_owner()
    async def sql(self, ctx: context.Context, pgType: str, *, sql: str):
        if pgType == 'exec':
            resp = await self.bot.db.execute(sql)
        elif pgType == 'fetch':
            resp = await self.bot.db.fetch(sql)
        elif pgType == 'fetchrow':
            resp = await self.bot.db.fetchrow(sql)
        elif pgType == 'fetchval':
            resp = await self.bot.db.fetchval(sql)
        else:
            return await ctx.error('Keine valider type')

        await ctx.embed(str(resp))

    @cmd()
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

    @grp(aliases=['maint'], case_insensitive=True)
    @commands.is_owner()
    async def maintenance(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            with open('utils/json/simpleStorage.json', 'r') as file:
                data = json.load(file)

            await ctx.embed(f'Maintenance: {data["maintenance"]}')

    @maintenance.command()
    async def activate(self, ctx: context.Context):
        with open('utils/json/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['maintenance'] = True
            json.dump(data, file)
            file.truncate()
            await ctx.embed('Maintenance: True')
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name='plyoox.net | ⚠ Wartungen'),
            status=discord.Status.idle)


    @maintenance.command()
    async def deactivate(self, ctx: context.Context):
        with open('utils/json/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['maintenance'] = False
            json.dump(data, file)
            file.truncate()
            await ctx.embed('Maintenance: False')

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='plyoox.net | +help'),
            status=discord.Status.online)

    @grp(case_insensitive=True)
    @commands.is_owner()
    async def globalban(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @globalban.command()
    async def add(self, ctx: context.Context, userID: int, *, Grund: str):
        await self.bot.db.execute('INSERT INTO extra.globalbans (userid, reason) VALUES ($1, $2)', userID, Grund)
        await ctx.embed('Der User wurde erfolgreich zur Globalban-Liste hinzugefügt.')

    @globalban.command()
    async def remove(self, ctx: context.Context, userID: int):
        await self.bot.db.execute('DELETE FROM extra.globalbans WHERE userid = $1', userID)
        await ctx.embed('Der User wurde erfolgreich von der Globalban-Liste entfernt.')

    @grp(case_insesitive=True)
    @commands.is_owner()
    async def commandCount(self, ctx: context.Context):
        pass

    @commandCount.command()
    async def reverse(self, ctx: context.Context):
        commandsCount = self.bot.commandsCount
        commandsCountSorted = sorted(commandsCount.items(), key=operator.itemgetter(1))
        commandsCountList = []
        commandRange = 15 and len(commandsCountSorted)

        for i in range(commandRange):
            command = commandsCountSorted[i]
            commandsCountList.append(f'**{command[0]}:** {command[1]}')

        await ctx.embed('\n'.join(commandsCountList))

    @commandCount.command()
    async def top(self, ctx: context.Context):
        commandsCount = self.bot.commandsCount
        commandsCountSorted = sorted(commandsCount.items(), key=operator.itemgetter(1))
        commandsCountSorted.reverse()
        commandsCountList = []
        commandRange = 15 and len(commandsCountSorted)

        for i in range(commandRange):
            command = commandsCountSorted[i]
            commandsCountList.append(f'**{command[0]}:** {command[1]}')

        await ctx.embed('\n'.join(commandsCountList))


def setup(bot):
    bot.add_cog(Owner(bot))
