import asyncio
import json
import random
import time

import discord
from discord.ext import commands, tasks

import main
from utils.ext import standards as std, checks
from utils.ext.cmds import grp


# BAN       0
# MUTE      1
# GIVEAWAY  2


class ParseTime:
    @classmethod
    def parse(cls, timeStr: str):
        if timeStr.endswith('d'):
            try:
                days = int(timeStr.replace('d', ''))
                if 30 < days <= 1:
                    raise TimeToLong()

                return days * 3600 * 24 + time.time()
            except:
                raise TypeError

        if timeStr.endswith('h'):
            try:
                hours = float(timeStr.replace('h', ''))
                if 48 < hours <= 0.25:
                    raise TimeToLong()

                return hours * 3600 + time.time()
            except:
                raise TypeError
        else:
            return None


class TimeToLong(Exception):
    pass


class Timers(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.checkTimers.start()

    @tasks.loop(minutes=15)
    async def checkTimers(self):
        entrys = await self.bot.db.fetch('SELECT * FROM extra.timers WHERE time - extract(EPOCH FROM now()) <= 900;')

        for entry in entrys:
            timerType = entry['type']
            endTime = entry['time']
            guildID = entry['sid']
            if timerType in [0, 1]:
                memberID = entry['objid']
                self.bot.loop.create_task(self.punishTimer(endTime, memberID, guildID, timerType))

            if timerType == 2:
                messageID = entry['objid']
                data = entry['data']
                self.bot.loop.create_task(self.giveawayTimer(endTime, messageID, data))

    @checkTimers.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    async def punishTimer(self, unbanTime: int, memberID: int, guildID: int, punishmentType: str):
        untilUnban = unbanTime - time.time()
        if unbanTime > 0:
            untilUnban = 0

        await asyncio.sleep(untilUnban)

        guild = self.bot.get_guild(guildID)
        self.bot.dispatch('punishment_runout', guild, memberID, punishmentType)

    async def giveawayTimer(self, endTime: int, messageID: int, data):

        untilEnd = endTime - time.time()
        if endTime > 0:
            untilEnd = 0

        await asyncio.sleep(untilEnd)

        data = json.loads(data)
        channel = self.bot.get_channel(data['channel'])
        message = await channel.fetch_message(messageID)
        self.bot.dispatch('giveaway_runout', message, data)

    @commands.Cog.listener()
    async def on_punishment_runout(self, guild: discord.Guild, memberID: int, punishType: int):
        if guild is None:
            return

        if punishType == 0:
            user = discord.Object(id=memberID)
            if user is None:
                return

            try:
                await guild.unban(user, reason='Tempban has expired')
            except discord.NotFound:
                pass
            await self.bot.db.execute(
                "DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = $3",
                guild.id, memberID, punishType)

        if punishType == 1:
            muteroleID: int = await self.bot.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', guild.id)
            muterole: discord.Role = guild.get_role(muteroleID)
            member: discord.Member = guild.get_member(memberID)

            if muterole is None or member is None:
                return

            try:
                await member.remove_roles(muterole)
            except discord.Forbidden:
                pass
            await self.bot.db.execute(
                "DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = $3",
                guild.id, memberID, punishType)

    @commands.Cog.listener()
    async def on_giveaway_runout(self, message: discord.Message, data):
        channel = message.channel
        reactions = message.reactions
        winners = []
        winnerCount = data['winner']
        win = data['winType']

        deleted: int = await self.bot.db.fetch('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2',
                                               message.guild.id, message.id)

        if deleted == 0:
            return

        for reaction in reactions:
            if reaction.emoji == '🎉':
                users = await reaction.users().flatten()
                users.remove(message.guild.me)
                if len(users) <= winnerCount:
                    winners = users
                else:
                    for _ in range(winnerCount):
                        user = random.choice(users)
                        winners.append(user)
                        users.remove(user)
                break

        winnerMention = ' '.join(member.mention for member in winners)
        await channel.send(f'Gewinner von {data["winType"]} {"ist" if len(winners) == 1 else "sind"}\n{winnerMention}')
        await message.edit(embed=discord.Embed(color=std.normal_color, title=f"🎉 Giveaway",
                                               description=f'**Gewinn:** {win}\n'
                                                           f'**Gewinner:** {winnerMention}.\n'
                                                           f'ID: {message.id}'))

    @grp(case_insensitive=True)
    @checks.isMod()
    async def giveaway(self, ctx):
        pass

    @giveaway.command()
    async def start(self, ctx, duration: str, winner: int, channel: discord.TextChannel, *, win: str):
        unixTime: float = ParseTime.parse(duration)
        data = {
            'winner': winner,
            'winType': win,
            'channel': channel.id
        }

        embed: discord.Embed = discord.Embed(color=std.normal_color,
                                             title=f'🎉 Giveaway',
                                             description=f'**Gewinn:** {win}\n'
                                                         'Reagiere mit 🎉 um dem Giveaway beizutreten.\n')

        msg: discord.Message = await channel.send(embed=embed)
        await msg.add_reaction('🎉')
        await ctx.send(embed=std.getEmbed('Das Giveaway wurde gestartet.'))
        await msg.edit(embed=discord.Embed(color=std.normal_color,
                                           title=f"🎉 Giveaway",
                                           description=f'**Gewinn:** {win} ({winner} Gewinner)\n'
                                                       'Reagiere mit 🎉 um dem Giveaway beizutreten.\n'
                                                       f'ID: {msg.id}'))
        await ctx.db.execute(
            'INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, 2, $4)',
            ctx.guild.id, msg.id, unixTime, json.dumps(data)
        )

    @giveaway.command()
    async def stop(self, ctx, ID: int):
        data = await ctx.db.execute(
            'SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        if data is None:
            return await ctx.send(embed=std.getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.db.execute(
            'DELETE FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        await ctx.send(embed=std.getEmbed('Das Giveaway wurde abgebrochen.'))
        channel: discord.TextChannel = ctx.guild.get_channel(data['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            try:
                await msg.delete()
            except:
                pass

    @giveaway.command()
    async def end(self, ctx, ID):
        data = await ctx.db.execute(
            'SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        if data is None:
            await ctx.send(embed=std.getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.send(embed=std.getEmbed('Das Giveaway wurde abgebrochen.'))
        channel: discord.TextChannel = ctx.guild.get_channel(data['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            self.bot.dispatch('giveaway_runout', msg, data['data'])


def setup(bot):
    bot.add_cog(Timers(bot))