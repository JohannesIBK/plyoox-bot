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
from utils.ext import standards as std
from utils.ext.cmds import cmd, grp


class Owner(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        super().__init__()
        self.bot = bot

    # --------------------------------commands--------------------------------

    @cmd(hidden=True, aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx):
        """Listet alle Server auf"""

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
    async def load(self, ctx: commands.Context, cog):
        self.bot.load_extension(cog)
        await ctx.send(embed=std.getEmbed(f'Das Modul {cog} wurde geladen.'))

    @cmd(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, cog):
        self.bot.reload_extension(cog)
        await ctx.send(embed=std.getEmbed(f'Das Modul {cog} wurde neugeladen.'))

    @cmd(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, cog):
        self.bot.unload_extension(cog)
        await ctx.send(embed=std.getEmbed(f'Das Modul {cog} wurde entladen.'))

    @cmd(hidden=True)
    @commands.is_owner()
    async def addRole(self, ctx, Rolle: discord.Role):
        count = 0
        members = [member for member in ctx.guild.members if len(member.roles) == 1 and not member.bot]
        for member in members:
            if ctx.me.top_role > member.top_role:
                try:
                    await member.add_roles(Rolle)
                    count += 1
                except discord.Forbidden:
                    break
        await ctx.send(f'{count} haben den Rang erhalten.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def removeRole(self, ctx, Rolle: discord.Role):
        count = 0
        f_count = 0
        for member in Rolle.members:
            try:
                await member.remove_roles(Rolle)
                count += 1
            except discord.Forbidden:
                f_count += 1

        await ctx.send(f'{count} haben den entzogen bekommen, {f_count} haben den Rang behalten.')

    @cmd(hidden=True)
    @commands.is_owner()
    async def leave(self, ctx):
        await ctx.guild.leave()

    @cmd(hidden=True, aliases=['quit'])
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("Shutdown")
        await self.bot.logout()

    @cmd()
    @commands.is_owner()
    async def permissions(self, ctx):
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
    async def _eval(self, ctx, *, body: str):
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
    async def logdata(self, ctx):
        file = discord.File("discord.log", filename="discord.log")
        await ctx.send(file=file)

    @cmd()
    @commands.is_owner()
    async def setXP(self, ctx, memb: discord.Member, XP: int):
        await ctx.db.execute("UPDATE extra.levels SET xp = $1, time = 0 WHERE userid = $2 AND guildid = $3",
                             XP, memb.id, ctx.guild.id)

    @cmd()
    @commands.is_owner()
    async def setVersion(self, ctx, version: str):
        self.bot.version = version
        await ctx.send(embed=std.getEmbed('Die Version wurde zu {version} geändert.'))

    @cmd()
    @commands.is_owner()
    async def reloadLang(self, ctx):
        self.bot.get_cog('Help').helpText = json.load(codecs.open(r'others/help_de.json', encoding='utf-8'))
        await ctx.send(embed=std.getEmbed('Der Help-Text wurde reloadet.'))

    @cmd()
    @commands.is_owner()
    async def sql(self, ctx, pgType: str, *, sql: str):
        if pgType == 'exec':
            resp = await self.bot.db.execute(sql)
        elif pgType == 'fetch':
            resp = await self.bot.db.fetch(sql)
        elif pgType == 'fetchrow':
            resp = await self.bot.db.fetchrow(sql)
        elif pgType == 'fetchval':
            resp = await self.bot.db.fetchval(sql)
        else:
            return await ctx.send(embed=std.getErrorEmbed('Keine valider type'))

        await ctx.send(embed=std.getEmbed(str(resp)))

    @cmd()
    @commands.is_owner()
    async def reloadutils(self, ctx, name: str):
        try:
            module_name = importlib.import_module(name)
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f"Couldn't find module named **{name}**")

        except Exception as e:
            return await ctx.send(f'```py\n{e}{traceback.format_exc()}\n```')

        await ctx.send(f"Reloaded module **{name}**")

    @grp(aliases=['maint'], case_insensitive=True)
    @commands.is_owner()
    async def maintenance(self, ctx):
        if ctx.invoked_subcommand is None:
            with open('others/simpleStorage.json', 'r') as file:
                data = json.load(file)

            await ctx.send(embed=std.getEmbed(f'Maintenance: {data["maintenance"]}'))

    @maintenance.command()
    async def activate(self, ctx):
        with open('others/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['maintenance'] = True
            json.dump(data, file)
            file.truncate()
            await ctx.send(embed=std.getEmbed('Maintenance: True'))
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name='plyoox.net | ⚠ Wartungen'),
            status=discord.Status.idle)


    @maintenance.command()
    async def deactivate(self, ctx):
        with open('others/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['maintenance'] = False
            json.dump(data, file)
            file.truncate()
            await ctx.send(embed=std.getEmbed('Maintenance: False'))

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='plyoox.net | +help'),
            status=discord.Status.online)

    @grp(case_insensitive=True)
    @commands.is_owner()
    async def globalban(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @globalban.command()
    async def add(self, ctx, user: discord.User, *, Grund: str):
        await self.bot.db.execute('INSERT INTO extra.globalbans (userid, reason) VALUES ($1, $2)', user.id, Grund)
        await ctx.send('Der User wurde erfolgreich zur Globalban-Liste hinzugefügt.')

    @globalban.command()
    async def remove(self, ctx, user: discord.User):
        await self.bot.db.execute('DELETE FROM extra.globalbans WHERE userid = $1', user.id)
        await ctx.send('Der User wurde erfolgreich von der Globalban-Liste entfernt.')

    @grp(case_insesitive=True)
    @commands.is_owner()
    async def commandCount(self, ctx):
        pass

    @commandCount.command()
    async def reverse(self, ctx):
        commandsCount = self.bot.commandsCount
        commandsCountSorted = sorted(commandsCount.items(), key=operator.itemgetter(1))
        commandsCountList = []
        commandRange = 15 and len(commandsCountSorted)

        for i in range(commandRange):
            command = commandsCountSorted[i]
            commandsCountList.append(f'**{command[0]}:** {command[1]}')

        await ctx.send(embed=std.getEmbed('\n'.join(commandsCountList)))

    @commandCount.command()
    async def top(self, ctx):
        commandsCount = self.bot.commandsCount
        commandsCountSorted = sorted(commandsCount.items(), key=operator.itemgetter(1))
        commandsCountSorted.reverse()
        commandsCountList = []
        commandRange = 15 and len(commandsCountSorted)

        for i in range(commandRange):
            command = commandsCountSorted[i]
            commandsCountList.append(f'**{command[0]}:** {command[1]}')

        await ctx.send(embed=std.getEmbed('\n'.join(commandsCountList)))


def setup(bot):
    bot.add_cog(Owner(bot))
