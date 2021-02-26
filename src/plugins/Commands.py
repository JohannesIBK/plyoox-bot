import asyncio
import datetime
from collections import defaultdict

import discord
from discord.ext import commands

import main
from utils.ext import standards as std


# EVERYONE ROLE USER
from utils.ext.context import Context


class Commands(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.cooldowns = defaultdict()

    async def command_list(self, ctx: Context):
        lang = await ctx.lang(module="commands")
        msg_splited = ctx.message.content.split(" ")
        command_name = msg_splited[0].replace(ctx.prefix, '').lower()
        if str(ctx.bot.user.id) in command_name:
            command_name = msg_splited[1]

        mentions = [False, False, False]
        msg = None

        command = await self.bot.db.fetchrow(
            "SELECT c.*, m.commands FROM extra.commands c LEFT JOIN config.modules m "
            "ON c.sid = m.sid WHERE c.sid = $1 AND c.name = $2",
            ctx.guild.id, command_name)
        if command is None or not command['commands']:
            return

        if command['cooldown']:
            current = ctx.message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
            if ctx.guild.id in self.cooldowns:
                if command['name'] in self.cooldowns[ctx.guild.id]:
                    bucket = self.cooldowns[ctx.guild.id][command['name']].get_bucket(
                        message=ctx.message)
                    if bucket.update_rate_limit(current=current):
                        return await ctx.error(lang["error.cooldown"])
                else:
                    self.cooldowns[ctx.guild.id][command['name']] = commands.CooldownMapping\
                        .from_cooldown(1, command['cooldown'], commands.BucketType.member)
                    self.cooldowns[ctx.guild.id][command['name']].get_bucket(message=ctx.message)\
                        .update_rate_limit(current=current)
            else:
                self.cooldowns.update({ctx.guild.id: {command['name']: commands.CooldownMapping
                    .from_cooldown(
                    1, command['cooldown'], commands.BucketType.member)}})
                self.cooldowns[ctx.guild.id][command['name']].get_bucket(message=ctx.message)\
                    .update_rate_limit(current=current)

        if command['ignoredroles']:
            user_roles = [role.id for role in ctx.author.roles]
            if any(role in user_roles for role in command['ignoredroles']):
                return await ctx.error(lang["error.notallowed"])

        if command['ignoredchannels']:
            if ctx.channel.id in command['ignoredchannels']:
                return await ctx.error(lang["error.forbiddenchannel"])

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
                                     allowed_mentions=discord.AllowedMentions(everyone=mentions[0],
                                                                              roles=mentions[1],
                                                                              users=mentions[2]))
            else:
                msg = await ctx.send(command['content'],
                                     allowed_mentions=discord.AllowedMentions(everyone=mentions[0],
                                                                              roles=mentions[1],
                                                                              users=mentions[2]))

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


def setup(bot):
    bot.add_cog(Commands(bot))
