import asyncio
import datetime
from collections import defaultdict

import discord
from discord.ext import commands

import main
from utils.ext import checks, standards as std, context
from utils.ext.cmds import grp


# EVERYONE ROLE USER

class Commands(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.cooldowns = defaultdict()

    async def command_list(self, ctx: context.Context):
        msgSplited = ctx.message.content.split(" ")[0]
        commandName = msgSplited.replace(ctx.prefix, '').lower()
        mentions = [ False, False, False ]
        msg = None

        command = await self.bot.db.fetchrow(
            "SELECT c.*, m.commands FROM extra.commands c LEFT JOIN config.modules m ON c.sid = m.sid WHERE c.sid = $1 AND c.name = $2",
            ctx.guild.id, commandName)
        if command is None or not command['commands']:
            return

        if command['cooldown']:
            current = ctx.message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
            if ctx.guild.id in self.cooldowns:
                if command['name'] in self.cooldowns[ctx.guild.id]:
                    bucket = self.cooldowns[ctx.guild.id][command['name']].get_bucket(message=ctx.message)
                    if bucket.update_rate_limit(current=current):
                        return await ctx.error('Der Command ist auf Cooldown.')
                else:
                    self.cooldowns[ctx.guild.id][command['name']] = commands.CooldownMapping.from_cooldown(
                        1, command['cooldown'], commands.BucketType.member)
                    self.cooldowns[ctx.guild.id][command['name']].get_bucket(message=ctx.message).update_rate_limit(current=current)
            else:
                self.cooldowns.update({ctx.guild.id: {command['name']: commands.CooldownMapping.from_cooldown(
                        1, command['cooldown'], commands.BucketType.member)}})
                self.cooldowns[ctx.guild.id][command['name']].get_bucket(message=ctx.message).update_rate_limit(current=current)

        if command['ignoredroles']:
            userRoles = [ role.id for role in ctx.author.roles ]
            if any(role in userRoles for role in command['ignoredroles']):
                return await ctx.error('Du darfst diesen Command nicht verwenden.')

        if command['ignoredchannels']:
            if ctx.channel.id in command['ignoredchannels']:
                return await ctx.error('Du darfst diesen Command in diesem Channel nicht verwenden.')

        if command['role']:
            role = ctx.guild.get_role(command['role'])
            if role is None:
                return
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
            else:
                await ctx.author.add_roles(role)

        if command['mentions']:
            mentions = command['mentions']

        if command['content']:
            if command['embed']:
                embed = discord.Embed(color=std.plyoox_color, description=command['content'])
                msg = await ctx.send(embed=embed,
                                     allowed_mentions=discord.AllowedMentions(everyone=mentions[0], roles=mentions[1], users=mentions[2]))
            else:
                msg = await ctx.send(command['content'],
                                     allowed_mentions=discord.AllowedMentions(everyone=mentions[0], roles=mentions[1], users=mentions[2]))

        if command['delete'] is not None and msg is not None:
            await asyncio.sleep(command['delete'])
            await ctx.message.delete()
            if command['content']:
                await msg.delete()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):        
        if msg.author.bot:
            return
        
        if msg.guild is None:
            return

        if not isinstance(msg.author, discord.Member):
            return

        ctx = await self.bot.get_context(msg)
        if ctx.command:
            return

        config = await self.bot.cache.get(msg.guild.id)
        if msg.content.startswith(tuple(config.prefix)):
            await self.command_list(ctx)

    @grp(name="command", aliases=["cmd", "cmds"])
    @checks.isAdmin()
    async def command_cmd(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), "command")

    @command_cmd.command()
    async def add(self, ctx: context.Context, name: str, *, content: str):
        name = name.lower()

        all_commands = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)
        if all_commands is not None:
            if len(all_commands) > 50:
                return await ctx.error('Der Server darf maximal 50 Commands besitzen.')

        if self.bot.get_command(name) is not None:
            return await ctx.error('Dieser Command darf nicht erstellt werden.')

        cmd = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is not None:
            return await ctx.error('Dieser Command existiert bereits.')

        await ctx.db.execute("INSERT INTO extra.commands (sid, name, content) VALUES ($1, $2, $3)", ctx.guild.id, name, content)
        await ctx.embed('Der Command wurde erfolgreich hinzugefügt.')

    @command_cmd.command()
    async def edit(self, ctx: context.Context, name: str, *, content: str):
        name = name.lower()

        cmd = await ctx.db.fetchval("SELECT name, content FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is None:
            return await ctx.error('Der Command wurde nicht gefunden.')

        await ctx.db.execute("UPDATE extra.commands SET content = $1 WHERE sid = $2 AND name = $3", content, ctx.guild.id, name)
        await ctx.embed('Der Command wurde erfolgreich bearbeitet.')

    @command_cmd.command(aliases=['delete', 'del'])
    async def remove(self, ctx: context.Context, name):
        name = name.lower()

        all_commands = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)

        if not all_commands:
            return await ctx.error('Der Server besitzt keine Commands.')

        cmd = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is None:
            return await ctx.error('Der Command wurde nicht gefunden.')

        await ctx.db.execute("DELETE FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)
        await ctx.embed('Der Command wurde erfolgreich entfernt.')

    @command_cmd.command()
    async def list(self, ctx: context.Context):
        all_commands = await ctx.db.fetch("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)

        if not all_commands:
            return await ctx.error('Der Server besitzt keine Commands.')

        await ctx.embed(", ".join(f'{cmd["name"]}' for cmd in all_commands))


def setup(bot):
    bot.add_cog(Commands(bot))
