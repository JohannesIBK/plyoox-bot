import argparse
import datetime
import io
import re
import shlex
from typing import Union

import discord
from discord.ext import commands

import main
from utils.automod import add_points
from utils.automod import automod
from utils.enums.Timer import TimerType
from utils.ext import checks
from utils.ext import logs
from utils.ext import standards as std
from utils.ext.cmds import cmd
from utils.ext.cmds import grp
from utils.ext.context import Context
from utils.ext.converters import ActionReason
from utils.ext.converters import AdvancedMember
from utils.ext.converters import BannedMember
from utils.ext.errors import FakeArgument
from utils.ext.time import FutureTime


linkRegex = re.compile(
    r'((https?://(www\.)?|www\.)[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})', re.IGNORECASE)


def can_execute_action(ctx, user, target):
    return user.id == ctx.bot.owner_id or \
           user == ctx.guild.owner or \
           user.top_role > target.top_role


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class Moderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot: main.Plyoox = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if msg.guild is None:
            return

        ctx = await self.bot.get_context(msg)
        await automod(ctx)

    @staticmethod
    async def can_punish_user(ctx: Context,
                              user: Union[discord.Member, discord.User, AdvancedMember]):
        if isinstance(user, discord.User):
            return True

        if user.id == ctx.bot.user.id:
            return

        if user.guild_permissions.manage_guild:
            return False

        cache = await ctx.cache.get(ctx.guild.id)
        roles = cache.automod.config.modroles
        roles.extend(cache.automod.config.helperroles)
        if any(role in roles for role in [role.id for role in user.roles]):
            return False

        return True

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: Context, user: AdvancedMember, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang['multi.error.notallowed'])

        await ctx.guild.ban(user=user, reason=reason.reason if reason is not None else None, delete_message_days=1)
        await ctx.embed(lang['ban.message'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("ban", reason, lang, mod=ctx.author, user=user)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='ban')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: Context, user: discord.Member, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang['multi.error.notallowed'])

        await ctx.guild.kick(user, reason=reason.reason if reason is not None else None)
        await ctx.embed(lang['kick.message'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("kick", reason, lang, mod=ctx.author, user=user)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='kick')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, ctx: Context, user: discord.Member, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang['multi.error.notallowed'])

        await ctx.guild.ban(user=user, reason=reason.reason if reason is not None else None, delete_message_days=1)
        await ctx.guild.unban(user=user, reason=lang['softban.reason'])

        await ctx.embed(lang['kick.message'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("kick", reason, lang, mod=ctx.author, user=user)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='kick')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["multi.error.notallowed"])

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["multi.error.nomuterole"])

        await user.add_roles(config.automod.config.muterole)
        await ctx.embed(lang["mute.perm.message"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("mute", reason, lang, mod=ctx.author, user=user)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='mute')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd(aliases=["tmute"])
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(self, ctx: Context, user: discord.Member, time: FutureTime, *,
                       reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["multi.error.notallowed"])

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["multi.error.nomuterole"])

        timers = self.bot.get_cog('Timers')
        await timers.create_timer(ctx.guild.id, date=time.dt, object_id=user.id,
                                  type=TimerType.MUTE.value)
        await user.add_roles(config.automod.config.muterole)

        await ctx.embed(lang["mute.temp.message"].format(u=str(user), r=reason, d=std.fixTimeDelta(time.delta)),
                        delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("tempmute", reason, lang, mod=ctx.author, user=user,
                                 duration=time.delta)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='mute',
                                 duration=time.delta)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["multi.error.nomuterole"])

        mute = await ctx.db.fetchrow(
            "SELECT objid FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = $3",
            ctx.guild.id, user.id, TimerType.MUTE.value)
        if config.automod.config.muterole not in user.roles and mute is None:
            return await ctx.error(lang["unmute.error.notmuted"])

        if config.automod.config.muterole in user.roles:
            await user.remove_roles(config.automod.config.muterole, reason=lang["word.unmute"])

        if mute is not None:
            await ctx.db.execute(
                "DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = $3",
                ctx.guild.id, user.id, TimerType.MUTE.value)

        await ctx.embed(lang["unmute.message"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("unmute", reason, lang, mod=ctx.author, user=user)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed)

    @cmd(aliases=["tban"])
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def tempban(self, ctx: Context, user: AdvancedMember, time: FutureTime, *,
                      reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["multi.error.notallowed"])

        timers = self.bot.get_cog('Timers')
        await timers.create_timer(ctx.guild.id, date=time.dt, object_id=user.id,
                                  type=TimerType.BAN.value)
        await ctx.guild.ban(user=user, reason=reason.reason if reason is not None else None, delete_message_days=1)

        await ctx.embed(lang["ban.temp.message"].format(u=str(user), r=reason.reason if reason is not None else None, d=std.fixTimeDelta(time.delta)),
                        delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("tempban", reason, lang, mod=ctx.author, user=user,
                                 duration=time.delta)
        user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='ban',
                                 duration=time.delta)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: Context, user: BannedMember, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await ctx.guild.unban(user.user, reason=reason.reason if reason is not None else None)

        await ctx.embed(lang["unban.message"].format(u=str(user.user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("unban", reason, lang, mod=ctx.author, user=user.user)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def multiban(self, ctx: Context, users: commands.Greedy[AdvancedMember], *,
                       reason: ActionReason = None):
        lang = await ctx.lang()
        total_members = len(users)
        if total_members == 0:
            raise commands.MissingRequiredArgument(FakeArgument('users'))

        confirm = await ctx.prompt(lang["multiban.prompt"].format(c=total_members), reacquire=False)
        if not confirm:
            return await ctx.embed(lang["massban.message.abort"])

        count = 0
        for user in users:
            try:
                await ctx.guild.ban(user, reason=reason.reason if reason is not None else None)
                count += 1
            except discord.HTTPException:
                pass

        fmt = "\n".join(lang["massban.memberlist.message"]
                        .format(id=m.id, j=m.joined_at, c=m.created_at, m=str(m)) for m in users)
        content = f'{lang["massban.word.usercount"]}: {len(users)}\n{fmt}'
        file = discord.File(io.BytesIO(content.encode('utf-8')), filename='members.txt')

        embed = std.cmdEmbed("massban", reason, lang, mod=ctx.author, amount=len(users))
        await logs.createCmdLog(ctx, embed=embed, file=file)

    @cmd()
    @checks.isMod(helper=True)
    async def warn(self, ctx: Context, user: discord.Member, points: int, *,
                   reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["multi.error.notallowed"])

        if points <= 0 or points > 20:
            return await ctx.error(lang["warn.error.points"])

        await add_points(ctx, points, reason, user=user)
        await ctx.embed(lang["warn.message"].format(u=str(user), r=reason.reason if reason is not None else None, p=str(points)),
                        delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    async def points(self, ctx: Context, user: discord.Member):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)
        if not config or not config.automod or config.automod.config.maxpoints is None:
            await ctx.error(lang["points.error.notset"])

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["multi.error.notallowed"])

        points = await self.bot.db.fetchval(
            'SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2', user.id,
            ctx.guild.id)
        if points is None:
            return await ctx.error(lang["points.error.nopoints"])

        await ctx.embed(lang["points.message"].format(u=str(user), p=str(points),
                                                      m=str(config.automod.config.maxpoints)),
                        delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    async def resetPoints(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        await ctx.bot.db.execute('DELETE FROM automod.users WHERE sid = $1 AND uid = $2',
                                 ctx.guild.id, user.id)
        await ctx.embed(lang["pointsreset.message"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("resetPoints", reason.reason if reason is not None else None, lang, mod=ctx.author, user=user)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed)

    @cmd(aliases=['slow', 'sm'])
    @checks.isMod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(rate=2, per=15, type=commands.BucketType.channel)
    async def slowmode(self, ctx: Context, seconds=0):
        lang = await ctx.lang(utils=True)

        if seconds < 0 or seconds > 21600:
            return await ctx.error(lang["slowmode.error.maxseconds"])
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.message.delete()
        await ctx.embed(lang["slowmode.message"].format(s=str(seconds)), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod(helper=True)
    async def check(self, ctx: Context, user: Union[BannedMember, discord.Member]):
        lang = await ctx.lang(utils=True)

        if not isinstance(user, discord.Member):
            ban_data = await ctx.bot.db.fetchrow(
                "SELECT * FROM extra.timers WHERE objid = $1 AND sid = $2 AND type = $3",
                user.user.id, ctx.guild.id, TimerType.BAN.value)
            if ban_data is None:
                return await ctx.embed(lang["check.ban.perma"].format(r=user.reason))
            else:
                timestamp = datetime.datetime.fromtimestamp(ban_data['time']).strftime(
                    lang["date.format.large"])
                await ctx.embed(lang["check.ban.temp"].format(d=timestamp, r=user.reason))
        else:
            embed = discord.Embed(color=std.normal_color)
            mute_data = await ctx.bot.db.fetchrow(
                "SELECT * FROM extra.timers WHERE objid = $1 AND sid = $2 AND type = $3",
                user.id, ctx.guild.id, TimerType.MUTE.value)
            punishments = await ctx.bot.db.fetch(
                "SELECT * FROM automod.users WHERE uid = $1 AND sid = $2",
                user.id, ctx.guild.id)

            if mute_data:
                timestamp = datetime.datetime.utcfromtimestamp(mute_data['time']).strftime(
                    lang["date.format.large"])
                embed.description = lang["check.mute.temp"].format(d=timestamp,
                                                                   r=mute_data.get("reason"))
            elif punishments:
                punishment_list = [f'{pm["reason"]} [{pm["points"]}]' for pm in punishments]
                embed.add_field(name=lang["check.punish"].format(p=str(len(punishment_list))),
                                value='\n'.join(punishment_list))
            else:
                return await ctx.embed(lang["check.nopunish"])
            await ctx.send(embed=embed)

    @grp(invoke_without_command=True, aliases=["remove", "purge", "p"])
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, amount: int, *, reason: ActionReason = None):
        if ctx.invoked_subcommand is None:
            if amount is None:
                return await ctx.send_help(ctx.command)

            lang = await ctx.lang(utils=True)
            await self.do_removal(ctx, amount, lambda m: True, lang, reason)

    @staticmethod
    async def do_removal(ctx: Context, limit: int, predicate, lang, reason=None, *, before=None,
                         after=None):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        if limit > 2000 or limit < 1:
            return await ctx.error(lang['clear.error.amount'])

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        deleted = len(deleted)

        await ctx.embed(lang['clear.message.deleted'].format(a=deleted), delete_after=5)
        await logs.createCmdLog(
            ctx, std.cmdEmbed("clear", reason, lang, mod=ctx.author, amount=deleted))

    @clear.command()
    async def embeds(self, ctx, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.embeds), lang, reason)

    @clear.command()
    async def files(self, ctx, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.attachments), lang, reason)

    @clear.command()
    async def images(self, ctx, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.embeds) or len(m.attachments), lang,
                              reason)

    @clear.command(name='all')
    async def _remove_all(self, ctx, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: True, lang, reason)

    @clear.command()
    async def user(self, ctx, amount: int, user: discord.Member, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: m.author == user, lang, reason)

    @clear.command()
    async def contains(self, ctx, amount: int, *, string: str):
        lang = await ctx.lang(utils=True)
        if len(string) < 3:
            return await ctx.send(lang["remove.error.minlength"])

        await self.do_removal(ctx, amount, lambda m: string in m.content, lang)

    @clear.command(name='bot', aliases=['bots'])
    async def _bot(self, ctx, amount: int, prefix=None, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (
                        prefix and m.content.startswith(prefix))

        await self.do_removal(ctx, amount, predicate, lang, reason)

    @clear.command(name='emoji', aliases=['emojis'])
    async def _emoji(self, ctx, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        custom_emoji = re.compile(r'<a?:[a-zA-Z0-9_]+:([0-9]+)>')

        await self.do_removal(ctx, amount, lambda m: custom_emoji.search(m.content), lang, reason)

    @clear.command(name='reactions')
    async def _reactions(self, ctx, amount: int):
        lang = await ctx.lang(utils=True)
        if amount > 2000:
            return await ctx.error(lang['clear.error.amount'])

        total_reactions = 0
        async for message in ctx.history(limit=amount, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.embed(lang['remove.message.reactions'].format(a=total_reactions), delete_after=5)

    @clear.command(name="links")
    async def _links(self, ctx: Context, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if amount > 2000:
            return await ctx.error(lang['clear.error.amount'])

        await self.do_removal(ctx, amount, lambda m: linkRegex.search(m.content), lang, reason)

    @clear.command()
    async def custom(self, ctx, *, args: str):
        """A more advanced purge command.
        This command uses a powerful "command line" syntax.
        Most options support multiple values to indicate 'any' match.
        If the value has spaces it must be quoted.
        The messages are only deleted if all options are met unless
        the `--or` flag is passed, in which case only if any is met.
        The following options are valid.
        `--user`: A mention or name of the user to remove.
        `--contains`: A substring to search for in the message.
        `--starts`: A substring to search if the message starts with.
        `--ends`: A substring to search if the message ends with.
        `--search`: How many messages to search. Default 100. Max 2000.
        `--after`: Messages must come after this message ID.
        `--before`: Messages must come before this message ID.
        Flag options (no arguments):
        `--bot`: Check if it's a bot user.
        `--embeds`: Check if the message has embeds.
        `--files`: Check if the message has attachments.
        `--emoji`: Check if the message has custom emoji.
        `--reactions`: Check if the message has reactions
        `--or`: Use logical OR for all options.
        `--not`: Use logical NOT for all options.
        """
        lang = await ctx.lang(utils=True)

        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--user', nargs='+')
        parser.add_argument('--contains', nargs='+')
        parser.add_argument('--starts', nargs='+')
        parser.add_argument('--ends', nargs='+')
        parser.add_argument('--or', action='store_true', dest='_or')
        parser.add_argument('--not', action='store_true', dest='_not')
        parser.add_argument('--emoji', action='store_true')
        parser.add_argument('--bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('--search', type=int)
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            await ctx.send(str(e))
            return

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    await ctx.send(str(e))
                    return

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args._or else any

        def predicate(m):
            r = op(p(m) for p in predicates)
            if args._not:
                return not r
            return r

        if args.after:
            if args.search is None:
                args.search = 2000

        if args.search is None:
            args.search = 100

        args.search = max(0, min(2000, args.search))
        await self.do_removal(ctx, args.search, predicate, lang, before=args.before,
                              after=args.after)

    @cmd(aliases=['banmatch'])
    @checks.isAdmin()
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx: Context, *, args):
        lang = await ctx.lang()

        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--channel', '-c')
        parser.add_argument('--reason', '-r')
        parser.add_argument('--search', type=int, default=100)
        parser.add_argument('--regex')
        parser.add_argument('--no-avatar', action='store_true')
        parser.add_argument('--no-roles', action='store_true')
        parser.add_argument('--created', type=int)
        parser.add_argument('--joined', type=int)
        parser.add_argument('--joined-before', type=int)
        parser.add_argument('--joined-after', type=int)
        parser.add_argument('--contains')
        parser.add_argument('--starts')
        parser.add_argument('--ends')
        parser.add_argument('--match')
        parser.add_argument('--show', action='store_true')
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            return await ctx.error(str(e))

        members = []

        if args.channel:
            channel = await commands.TextChannelConverter().convert(ctx, args.channel)
            before = args.before and discord.Object(id=args.before)
            after = args.after and discord.Object(id=args.after)
            predicates = []
            if args.contains:
                predicates.append(lambda m: args.contains in m.content)
            if args.starts:
                predicates.append(lambda m: m.content.startswith(args.starts))
            if args.ends:
                predicates.append(lambda m: m.content.endswith(args.ends))
            if args.match:
                try:
                    _match = re.compile(args.match)
                except re.error as e:
                    return await ctx.error(lang["massban.error.regex"].format(e=str(e)))
                else:
                    predicates.append(lambda m, x=_match: x.match(m.content))
            if args.embeds:
                predicates.append(args.embeds)
            if args.files:
                predicates.append(args.files)

            async for message in channel.history(limit=min(max(1, args.search), 2000),
                                                 before=before, after=after):
                if all(p(message) for p in predicates):
                    members.append(message.author)
        else:
            if ctx.guild.chunked:
                members = ctx.guild.members
            else:
                async with ctx.typing():
                    await ctx.guild.chunk(cache=True)
                members = ctx.guild.members

        # member filters
        predicates = [
            lambda m: m.id != ctx.author.id,
            lambda m: can_execute_action(ctx, ctx.author, m),  # Only if applicable
            lambda m: not m.bot,  # No bots
            lambda m: m.discriminator != '0000',  # No deleted users
        ]

        converter = commands.MemberConverter()

        if args.regex:
            try:
                _regex = re.compile(args.regex)
            except re.error as e:
                return await ctx.error(lang["massban.error.regex"].format(e=str(e)))
            else:
                predicates.append(lambda m, x=_regex: x.match(m.name))

        if args.no_avatar:
            predicates.append(lambda m: m.avatar is None)
        if args.no_roles:
            predicates.append(lambda m: len(getattr(m, 'roles', [])) <= 1)

        now = datetime.datetime.utcnow()
        now = datetime.datetime.utcnow()
        if args.created:
            def created(_member, *, offset=now - datetime.timedelta(minutes=args.created)):
                return _member.created_at > offset

            predicates.append(created)
        if args.joined:
            def joined(_member, *, offset=now - datetime.timedelta(minutes=args.joined)):
                if isinstance(_member, discord.User):
                    # If the member is a user then they left already
                    return True
                return _member.joined_at and _member.joined_at > offset

            predicates.append(joined)
        if args.joined_after:
            _joined_after_member = await converter.convert(ctx, str(args.joined_after))

            def joined_after(_member, *, _other=_joined_after_member):
                return _member.joined_at and _other.joined_at and _member.joined_at > _other.joined_at

            predicates.append(joined_after)
        if args.joined_before:
            _joined_before_member = await converter.convert(ctx, str(args.joined_before))

            def joined_before(_member, *, _other=_joined_before_member):
                return _member.joined_at and _other.joined_at and _member.joined_at < _other.joined_at

            predicates.append(joined_before)

        members = {m for m in members if all(p(m) for p in predicates)}
        if len(members) == 0:
            return await ctx.error(lang["massban.error.noonefound"])

        if args.show:
            members = sorted(members, key=lambda m: m.joined_at or now)
            fmt = "\n".join(lang["massban.memberlist.message"]
                            .format(id=m.id, j=m.joined_at, c=m.created_at, m=str(m)) for m in
                            members)
            content = f'{lang["massban.word.usercount"]}: {len(members)}\n{fmt}'
            file = discord.File(io.BytesIO(content.encode('utf-8')), filename='members.txt')
            return await ctx.send(file=file)

        if args.reason is None:
            return await ctx.error(lang["massban.error.noreason"])
        else:
            reason: ActionReason = await ActionReason().convert(ctx, args.reason)

        confirm = await ctx.prompt(lang["massban.message.prompt"].format(m=str(len(members))))
        if not confirm:
            return await ctx.embed(lang["massban.message.abort"])

        count = 0
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason.reason if reason is not None else None)
            except discord.HTTPException:
                pass
            else:
                count += 1

        await ctx.embed(lang["massban.message.banned"].format(c=str(count), m=str(len(members))))

        embed = std.cmdEmbed('massban', reason, lang, mod=ctx.author, amount=len(members))
        embed.add_field(name=lang["massban.embed.users.name"],
                        value=lang["massban.embed.users.value"].format(c=str(count),
                                                                       m=str(len(members))))

        await logs.createCmdLog(ctx, embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
