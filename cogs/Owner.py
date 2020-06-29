import codecs
import datetime
import importlib
import io
import json
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands

import main
from utils.ext import standards
from utils.ext.cmds import cmd


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
    async def load(self, ctx: commands.Context, CogName: str = None):
        if CogName is not None:
            try:
                self.bot.reload_extension("cogs." + CogName)
            except commands.ExtensionNotLoaded:
                await ctx.send(embed=discord.Embed(color=discord.Color.red(),
                                                   description=f'Das Modul `{CogName}` konnte nicht gefunden werden.'))
            else:
                cog: commands.Cog = self.bot.get_cog(CogName)
                for cogCmd in cog.get_commands():
                    self.bot.get_all_commands.update({cogCmd.name.lower(): cogCmd})
                    for alias in cogCmd.aliases:
                        self.bot.get_all_commands.update({alias.lower(): cogCmd})
                await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                                   description=f'Das Modul `{CogName}` wurde neu geladen.'))
        else:
            for cogName in self.bot.cogs:
                try:
                    self.bot.reload_extension("cogs." + cogName)
                    cog: commands.Cog = self.bot.get_cog(cogName)
                    for cogCmd in cog.get_commands():
                        self.bot.get_all_commands.update({cogCmd.name.lower(): cogCmd})
                        for alias in cogCmd.aliases:
                            self.bot.get_all_commands.update({alias.lower(): cogCmd})
                except:
                    await ctx.send(f'```py\n{traceback.format_exc()}\n```')
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description=f'Alle Module wurden neu geladen.'))

    @cmd(hidden=True)
    @commands.is_owner()
    async def addRole(self, ctx, Rolle: discord.Role):
        """Gibt jedem auf dem Server eine Rolle."""
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
        """Entfernt jeden aus einer Rolle."""
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
        """Verlässt einen Server"""
        await ctx.guild.leave()

    @cmd(hidden=True, aliases=['quit'])
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Schaltet den Bot aus."""
        await ctx.send("Shutdown")
        await self.bot.logout()

    @cmd()
    @commands.is_owner()
    async def permissions(self, ctx):
        """Listet alle Berechtigungen auf."""
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

    @cmd(hidden=True)
    @commands.is_owner()
    async def toCopy(self, ctx):
        """Infos zum Kopieren von Servern."""
        embed = discord.Embed(title='Guild Copy Infos', color=0x3498db)
        embed.add_field(name='ServerID', value=f'{ctx.guild.id}')
        embed.add_field(name='Top-Role ID', value=ctx.guild.get_member(self.bot.user.id).top_role.id)
        await ctx.send(embed=embed)

    @cmd(pass_context=True, name='eval', aliases=["exec"])
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

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
    async def setXP(self, ctx, memb: discord.Member, Level: int, XP: int):
        await ctx.db.execute("UPDATE extra.levels SET xp = $1, lvl = $2, time = $3 WHERE userid = $4 AND guildid = $5",
                             XP, Level, 0, memb.id, ctx.guild.id)

    @cmd()
    @commands.is_owner()
    async def setVersion(self, ctx, version: str):
        self.bot.version = version
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'Die Version wurde zu {version} geändert.'))

    @cmd()
    @commands.is_owner()
    async def reloadLang(self, ctx):
        self.bot.get_cog('Help').helpText = json.load(codecs.open(r'others/help_de.json', encoding='utf-8'))
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'Der Help-Text wurde reloadet.'))

    @cmd()
    @commands.is_owner()
    async def sql(self, ctx, type: str, *, sql: str):
        if type == 'exec':
            resp = await self.bot.db.execute(sql)
        elif type == 'fetch':
            resp = await self.bot.db.fetch(sql)
        elif type == 'fetchrow':
            resp = await self.bot.db.fetchrow(sql)
        elif type == 'fetchval':
            resp = await self.bot.db.fetchval(sql)
        else:
            return await ctx.send(embed=standards.getErrorEmbed('Keine valider type'))

        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=str(resp)))

    @commands.command()
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


def setup(bot):
    bot.add_cog(Owner(bot))
