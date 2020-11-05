import asyncio
import datetime
import json
import random
import time

import asyncpg
import discord
from discord.ext import commands

import main
from utils.ext import standards as std, checks, context, logs
from utils.ext.cmds import grp
from utils.ext.context import Context
from utils.ext.time import FutureTime
from utils.ext.reminder import Timer


# BAN       0
# MUTE      1
# GIVEAWAY  2
# REMINDER  3


class Timers(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self._current_timer: Timer = None
        self._have_data = asyncio.Event(loop=bot.loop)
        self._task = bot.loop.create_task(self.dispatch_timers())

    async def get_active_timer(self, *, connection=None, days=7):
        con = connection or self.bot.db

        record = await con.fetchrow("SELECT * FROM extra.timers WHERE time < $1 ORDER BY time LIMIT 1", time.time() + days + 86400)
        return Timer.load_timer(record=record) if record else None

    async def wait_for_active_timers(self, *, days=7):
        async with self.bot.db.acquire(timeout=300) as con:
            timer = await self.get_active_timer(connection=con, days=days)
            if timer is not None:
                self._have_data.set()
                return timer

            self._have_data.clear()
            self._current_timer = None
            await self._have_data.wait()
            return await self.get_active_timer(connection=con, days=days)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                timer = self._current_timer = await self.wait_for_active_timers(days=40)
                now = datetime.datetime.utcnow().timestamp()

                if timer.time >= now:
                    to_sleep = timer.time - now
                    print(to_sleep)
                    await asyncio.sleep(to_sleep)
                print('instant')

                await self.call_timer(timer)
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def call_timer(self, timer):
        await self.bot.db.execute("DELETE FROM extra.timers WHERE id = $1", timer.id)
        self.bot.dispatch(f'{timer.type}_end', timer)

    async def short_timer(self, timer, delta):
        await asyncio.sleep(delta)
        self.bot.dispatch(f'{timer.type}_end', timer)

    async def create_timer(self, ctx: context.Context, *, date: datetime.datetime, objectID: int, type: str, data: dict = None):
        seconds = date.timestamp()
        delta = (date - datetime.datetime.utcnow()).total_seconds()
        timer = await Timer.create_timer(ctx.guild.id, time=seconds, object_id=objectID, type=type, data=data)

        if delta <= 60:
            self.bot.loop.create_task(self.short_timer(timer, delta))
            return timer

        timer_id = await ctx.db.execute(
            "INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            ctx.guild.id, objectID, seconds, type, data
        )

        timer.id = timer_id

        if delta <= (86400 * 40):
            self._have_data.set()

        if self._current_timer and seconds < self._current_timer.time:
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

        return timer

    @commands.Cog.listener()
    async def on_tempban_end(self, timer: Timer):
        user = discord.Object(timer.object_id)
        lang = await self.bot.lang(timer.sid, "moderation", utils=True)
        guild = self.bot.get_guild(timer.sid)
        if guild is None:
            return

        fake_context = context.FakeContext(self.bot, guild)
        ban = await guild.fetch_ban(user)
        await guild.unban(user=user, reason=lang["ban.temp.reason.expired"])
        mod_embed = std.cmdEmbed("unban", lang["ban.temp.reason.expired"], lang, user=ban.user, mod=fake_context.me)
        await logs.createLog(fake_context, mEmbed=mod_embed, automod=True)


    @commands.Cog.listener()
    async def on_tempmute_end(self, timer):
        guild = self.bot.get_guild(timer.sid)
        config = await self.bot.cache.get(timer.sid)
        if guild is None or config is None:
            return

        lang = await self.bot.lang(timer.sid, "moderation", utils=True)
        user = guild.get_member(timer.object_id)
        if user is None:
            return

        fake_context = context.FakeContext(self.bot, guild)
        mod_embed = std.cmdEmbed("unmute", lang["mute.temp.reason.unmute"], lang, user=user, mod=fake_context.me)
        await user.remove_roles(config.automod.config.muterole)
        await logs.createLog(fake_context, mEmbed=mod_embed, automod=True)

    @commands.Cog.listener()
    async def on_timer_end(self, timer: Timer):
        guild = self.bot.get_guild(timer.sid)
        lang = await self.bot.lang(timer.sid, "timers")
        channel = guild.get_channel(timer.data["channel_id"])
        member = await guild.fetch_member(timer.object_id)
        if channel is None or member is None:
            return

        message = lang["reminder.event.timermessage"].format(u=str(member), m=std.quote(timer.data["message"]))

        await channel.send(message, allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False))

    @commands.Cog.listener()
    async def on_giveaway_end(self, timer: Timer):
        lang = await self.bot.lang(timer.sid, "timers")
        guild = self.bot.get_guild(timer.sid)
        channel = guild.get_channel(timer.data["channel_id"])
        message = await channel.fetch_message(timer.object_id)
        if message is None:
            return

        reactions = message.reactions
        winners = []
        winnerCount = timer.data['winner']
        win = timer.data['winType']

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
            await channel.send(lang["giveaway.event.nowinners"].format(w=win))
            embed = discord.Embed(color=std.normal_color, title=win,
                                                   description=lang["giveaway.event.nowinners.edited"])
            embed.set_footer(text=lang["giveaway.embed.footer"].format(g=str(winnerCount), id=str(message.id)))
        else:
            winnerMention = ' '.join(member.mention for member in winners)
            if len(winners) == 1:
                await channel.send(lang["giveaway.event.message.single"].format(w=win, m=winnerMention),
                                   allowed_mentions=discord.AllowedMentions(users=True))

                await message.edit(embed=discord.Embed(color=std.normal_color, title=win,
                                                       description=lang["giveaway.event.edit.single"].format(w=winnerMention)))
            else:
                await channel.send(lang["giveaway.event.message.multiple"].format(w=win, m=winnerMention),
                                   allowed_mentions=discord.AllowedMentions(users=True))

                await message.edit(embed=discord.Embed(color=std.normal_color, title=win,
                                                       description=lang["giveaway.event.edit.multiple"].format(w=winnerMention)))
            roleID = await self.bot.db.fetchval('SELECT winnerrole FROM config.timers WHERE sid = $1', message.guild.id)
            role = message.guild.get_role(roleID)
            if role is not None:
                for winner in winners:
                    try:
                        await winner.add_roles(role)
                    except discord.Forbidden:
                        break

    @grp(case_insensitive=True)
    async def giveaway(self, ctx: context.Context):
        if not ctx.author.guild_permissions.administrator:
            manager = await ctx.db.fetchval('SELECT giveawaymanager FROM config.timers WHERE sid = $1', ctx.guild.id)
            if manager:
                userRoles = [role.id for role in ctx.author.roles]
                if not any(role in userRoles for role in manager):
                    raise commands.MissingPermissions(['giveawaymanager'])
            else:
                raise commands.MissingPermissions(['giveawaymanager'])

        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @giveaway.command()
    async def start(self, ctx: Context, duration: FutureTime, winner: int, channel: discord.TextChannel, *, win: str):
        lang = await ctx.lang()
        data = {
            'winner': winner,
            'winType': win,
            'channel': channel.id
        }

        embed = discord.Embed(color=std.normal_color, title=lang["giveaway.embed.title"],
                              description=lang["giveaway.embed.startdescription"])
        msg = await channel.send(embed=embed)
        await msg.add_reaction('🎉')
        await ctx.send(embed=std.getEmbed(lang["giveaway.message.started"]))
        embed = discord.Embed(color=std.normal_color, title=win,
                              description=lang["giveaway.embed.description"])
        embed.set_footer(text=lang["giveaway.embed.footer"].format(g=str(winner), id=str(msg.id)))
        embed.timestamp = duration.dt
        await msg.edit(embed=embed)
        await ctx.db.execute(
            "INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, 'giveaway', $4)",
            ctx.guild.id, msg.id, duration, json.dumps(data))

    @giveaway.command()
    async def stop(self, ctx: context.Context, ID: int):
        lang = await ctx.lang()
        data = await ctx.db.fetchrow('SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        if data is None:
            await ctx.error(lang["giveaway.error.wrongid"])

        await ctx.db.execute('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        await ctx.embed(lang["giveaway.message.stopped"])
        giveawayData = json.loads(data['data'])
        channel = ctx.guild.get_channel(giveawayData['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            try:
                await msg.delete()
            except:
                pass

    @giveaway.command()
    async def end(self, ctx: context.Context, ID: int):
        lang = await ctx.lang()
        data = await ctx.db.fetchrow('SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2', ctx.guild.id, ID)
        if data is None:
            await ctx.error(lang["giveaway.error.wrongid"])

        await ctx.embed(lang["giveaway.message.abort"])
        timer = Timer.load_timer(data)
        self.bot.dispatch('giveaway_end', timer)

    @grp(aliases=['timer'])
    @checks.isActive('timers')
    async def reminder(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @reminder.command(cooldown_after_parsing=True)
    @commands.cooldown(rate=2 , per=30.0, type=commands.BucketType.user)
    async def create(self, ctx: context.Context, duration: FutureTime, *, reason: str):
        lang = await ctx.lang()
        noreminder = await ctx.db.fetchval('SELECT noreminderrole FROM config.timers WHERE sid = $1', ctx.guild.id)
        if noreminder:
            if noreminder in [role.id for role in ctx.author.roles]:
                return await ctx.error(lang["reminder.error.forbidden"])

        timerCount = await ctx.db.fetchval(
            'SELECT count(*) FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ctx.author.id)

        if timerCount >= 25:
            await ctx.error(lang["reminder.error.maxtimer"])

        await ctx.db.execute(
            'INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, $4, $5)',
            ctx.guild.id, ctx.author.id, duration.dt.timestamp(),'timer', json.dumps({'message': reason, 'channel_id': ctx.channel.id}))

        await ctx.embed(lang["reminder.message.created"], delete_after=10)
        await ctx.message.delete(delay=10)

    @reminder.command()
    async def list(self, ctx: context.Context):
        lang = await ctx.lang()
        noreminder = await ctx.db.fetchval(
            'SELECT noreminderrole FROM config.timers WHERE sid = $1',
            ctx.guild.id)

        if noreminder:
            if noreminder in [role.id for role in ctx.author.roles]:
                return await ctx.error(lang["reminder.error.forbidden"])

        reminders = await ctx.db.fetch(
            'SELECT * FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ctx.author.id)

        if not reminders:
            return await ctx.error(lang["reminder.error.notimers"])

        timerListEmbed = discord.Embed(color=std.normal_color, title='Timer')
        timerListEmbed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        for timer in reminders:
            reason = json.loads(timer['data'])['message']
            timerListEmbed.add_field(name='TimerID: ' + str(timer['id']), value=f'```{reason}```')

        await ctx.send(embed=timerListEmbed)

    @reminder.command(alias=["delete"])
    async def remove(self, ctx: context.Context, ID: int):
        lang = await ctx.lang()
        deleted = await ctx.db.fetchval(
            'DELETE FROM extra.timers WHERE ID = $1 AND sid = $2 AND objid = $3',
            ID, ctx.guild.id, ctx.author.id)

        if deleted:
            return await ctx.embed(lang["reminder.message.deleted"])
        await ctx.error(lang["reminder.error.delete"])

def setup(bot):
    bot.add_cog(Timers(bot))