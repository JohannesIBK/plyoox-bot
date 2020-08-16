import asyncio
import datetime
import json
import random
import time

import discord
from discord.ext import commands, tasks

import main
from utils.ext import standards as std, checks, converters
from utils.ext.cmds import grp, cmd


# BAN       0
# MUTE      1
# GIVEAWAY  2
# REMINDER  3


class Timers(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.checkTimers.start()

    @tasks.loop(minutes=10)
    async def checkTimers(self):
        entrys = await self.bot.db.fetch('SELECT * FROM extra.timers WHERE time - extract(EPOCH FROM now()) <= 900;')

        for entry in entrys:
            timerType = entry['type']
            endTime = entry['time']
            guildID = entry['sid']
            if timerType in [0, 1]:
                self.bot.loop.create_task(self.punishTimer(endTime, entry['objid'], guildID, timerType))

            elif timerType == 2:
                self.bot.loop.create_task(self.giveawayTimer(endTime, entry['objid'], guildID, entry['data']))

            if timerType == 3:
                self.bot.loop.create_task(self.reminderTimer(endTime, entry['objid'], guildID, entry['data']))


    @checkTimers.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    async def punishTimer(self, unbanTime: int, memberID: int, guildID: int, punishmentType: int):
        untilUnban = unbanTime - time.time()
        if unbanTime < 0:
            untilUnban = 0

        await asyncio.sleep(untilUnban)

        guild = self.bot.get_guild(guildID)
        await self.bot.db.execute("DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = $3", guild.id, memberID, punishmentType)
        self.bot.dispatch('punishment_runout', guild, memberID, punishmentType)

    async def giveawayTimer(self, endTime: int, messageID: int, guildID: int, data):
        untilEnd = endTime - time.time()
        if endTime < 0:
            untilEnd = 0

        await asyncio.sleep(untilEnd)

        deleted = await self.bot.db.execute('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = 2', guildID, messageID)
        if deleted == 0:
            return

        data = json.loads(data)
        channel = self.bot.get_channel(int(data['channel']))
        message = await channel.fetch_message(messageID)
        self.bot.dispatch('giveaway_runout', message, json.loads(data))

    async def reminderTimer(self, endTime: int, memberID: int, guildID: int, data):
        untilEnd = endTime - time.time()
        if endTime < 0:
            untilEnd = 0

        await asyncio.sleep(untilEnd)

        await self.bot.db.execute('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = 3', guildID, memberID)

        data = json.loads(data)
        guild: discord.Guild = self.bot.get_guild(guildID)
        if guild is None:
            return
        member: discord.Member = guild.get_member(memberID)
        if member is None:
            return
        channel: discord.TextChannel = guild.get_channel(int(data['channelid']))
        try:
            await channel.send(f'Hier ist deine Erinnerung {member.mention}!', embed=std.getEmbed(data['message']))
        except discord.Forbidden:
            pass

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
            except:
                pass

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

    @commands.Cog.listener()
    async def on_giveaway_runout(self, message: discord.Message, data):
        channel = message.channel
        reactions = message.reactions
        winners = []
        winnerCount = data['winner']
        win = data['winType']

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

        if len(winners) == 0:
            await channel.send(f'Niemand hat teilgenommen. Es gibt keine Gewinner :(')
            await message.edit(embed=discord.Embed(color=std.normal_color, title=f"🎉 Giveaway",
                                                   description=f'**Gewinn:** {win}\n**Gewinner:** Keine Gewinner.\nID: {message.id}'))
        else:
            winnerMention = ' '.join(member.mention for member in winners)
            await channel.send(f'Gewinner von {data["winType"]} {"ist" if len(winners) == 1 else "sind"}\n{winnerMention}',
                               allowed_mentions=discord.AllowedMentions(users=True))
            await message.edit(embed=discord.Embed(color=std.normal_color, title=f"🎉 Giveaway",
                                                   description=f'**Gewinn:** {win}\n**Gewinner:** {winnerMention}.\nID: {message.id}'))
            roleID = await self.bot.db.fetchval('SELECT winnerrole FROM config.timers WHERE sid = $1', message.guild.id)
            role: discord.Role = message.guild.get_role(roleID)
            if role is not None:
                for winner in winners:
                    try:
                        await winner.add_roles()
                    except discord.Forbidden:
                        break

    @grp(case_insensitive=True)
    async def giveaway(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            manager = await ctx.db.fetchval('SELECT giveawaymanager FROM config.timers WHERE sid = $1', ctx.guild.id)
            if manager:
                userRoles = [role.id for role in ctx.author.roles]
                if not any(role in userRoles for role in manager):
                    raise commands.MissingPermissions(['administrator / giveawaymanager'])
            else:
                raise commands.MissingPermissions(['administrator / giveawaymanager-role'])

        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @giveaway.command()
    async def start(self, ctx, duration: converters.ParseTime, winner: int, channel: discord.TextChannel, *, win: str):
        data = {
            'winner': winner,
            'winType': win,
            'channel': channel.id
        }

        embed: discord.Embed = discord.Embed(color=std.normal_color, title=f'🎉 Giveaway', description=f'**Gewinn:** {win}\nReagiere mit 🎉 um dem Giveaway beizutreten.\n')
        msg: discord.Message = await channel.send(embed=embed)
        await msg.add_reaction('🎉')
        await ctx.send(embed=std.getEmbed('Das Giveaway wurde gestartet.'))
        embed = discord.Embed(color=std.normal_color,
                              title=f"🎉 Giveaway",
                              description=f'**Gewinn:** {win} ({winner} Gewinner)\nReagiere mit 🎉 um dem Giveaway beizutreten.\nID: {msg.id}')
        embed.set_footer(text=f'Endet um')
        # noinspection PyTypeChecker
        embed.timestamp = datetime.datetime.utcfromtimestamp(duration)
        await msg.edit(embed=embed)
        await ctx.db.execute(
            'INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, 2, $4)',
            ctx.guild.id, msg.id, duration, json.dumps(data))

    @giveaway.command()
    async def stop(self, ctx, ID: int):
        data = await ctx.db.fetchrow('SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        if data is None:
            return await ctx.send(embed=std.getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.db.execute('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        await ctx.send(embed=std.getEmbed('Das Giveaway wurde abgebrochen.'))
        giveawayData = json.loads(data['data'])
        channel: discord.TextChannel = ctx.guild.get_channel(giveawayData['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            try:
                await msg.delete()
            except:
                pass

    @giveaway.command()
    async def end(self, ctx, ID: int):
        data = await ctx.db.fetchrow('SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        if data is None:
            await ctx.send(embed=std.getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.send(embed=std.getEmbed('Das Giveaway wurde abgebrochen.'))
        giveawayData = json.loads(data['data'])
        channel: discord.TextChannel = ctx.guild.get_channel(giveawayData['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            self.bot.dispatch('giveaway_runout', msg, giveawayData)

    @cmd()
    @checks.isActive('timers')
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.user)
    async def reminder(self, ctx, duration: converters.ParseTime, *, reason: str):
        noreminder = await ctx.db.fetchval('SELECT noreminderrole FROM config.timers WHERE sid = $1', ctx.guild.id)
        if noreminder:
            if noreminder in [role.id for role in ctx.author.roles]:
                return await ctx.send(embed=std.getErrorEmbed('Du darfst keien Reminder verwenden.'))

        if reason is None:
            return await ctx.send(embed=std.getEmbed('Gib einen Grund für deinen Reminder an.'))

        await ctx.db.execute(
            'INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, $4, $5)',
            ctx.guild.id, ctx.author.id, duration, 3, json.dumps({'message': reason, 'channelid': ctx.channel.id}))

        await ctx.send(embed=std.getEmbed('Dein Timer wurde erstellt.'))


def setup(bot):
    bot.add_cog(Timers(bot))