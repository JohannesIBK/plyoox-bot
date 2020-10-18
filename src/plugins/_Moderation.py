import datetime

import argparse
import io
import re
import shlex
from typing import Union

import discord
from discord.ext import commands

import main
from utils import automod
from utils.ext import checks, logs, standards as std
from utils.ext.cmds import cmd, grp
from utils.ext.context import Context
from utils.ext.converters import ActionReason, BannedMember, AdvancedMember
from utils.ext.time import FutureTime

linkRegex = re.compile('((https?://(www\.)?|www\.)[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})', re.IGNORECASE)


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class Moderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot: main.Plyoox = bot

    @staticmethod
    async def can_punish_user(ctx: Context, user: Union[discord.Member, discord.User]):
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
            return await ctx.error(lang['errorPunishNotAllowed'])

        await ctx.guild.ban(user=user, reason=reason, delete_message_days=1)
        await ctx.embed(lang['userBan'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("ban", reason, lang, mod=ctx.author, user=user)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='ban')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: Context, user: discord.Member, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang['errorPunishNotAllowed'])

        await ctx.guild.kick(user, reason=reason)
        await ctx.embed(lang['userKick'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("kick", reason, lang, mod=ctx.author, user=user)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='kick')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, ctx: Context, user: discord.Member, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang['errorPunishNotAllowed'])

        await ctx.guild.ban(user=user, reason=reason, delete_message_days=1)
        await ctx.guild.unban(user=user, reason=lang['softbanUnban'])

        await ctx.embed(lang['userKick'].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("kick", reason, lang, mod=ctx.author, user=user)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='kick')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, amount: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        if amount > 2000 or amount < 0:
            return await ctx.error(lang['errorClearAmount'])

        messages = await ctx.channel.history(limit=amount + 1).flatten()
        content = '\n'.join(f'{msg.author} ({msg.author.id}): {msg.content}' for msg in messages)
        file = discord.File(io.BytesIO(content.encode()), 'messages.txt')
        await logs.createCmdLog(ctx, std.cmdEmbed("clear", reason, lang, mod=ctx.author, amount=amount), file)

        deleted_messages = await ctx.channel.purge(limit=amount + 1)
        await ctx.embed(lang['clearDeleted'].format(a=len(deleted_messages) - 1), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["errorPunishNotAllowed"])

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["noMuteRole"])

        await user.add_roles(config.automod.config.muterole)
        await ctx.embed(lang["muteSuccess"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("mute", reason, lang, mod=ctx.author, user=user)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='mute')
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(self, ctx: Context, user: discord.Member, time: FutureTime, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if not await self.can_punish_user(ctx, user):
            return await ctx.error(lang["errorPunishNotAllowed"])

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["noMuteRole"])

        timers = self.bot.get_cog('Timers')
        await timers.create_timer(ctx, date=time.dt, objectID=user.id, type='tempmute')
        await user.add_roles(config.automod.config.muterole)

        await ctx.embed(lang["tempmuteSuccess"].format(u=str(user), r=reason, d=time.delta), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("tempmute", reason, lang, mod=ctx.author, user=user, duration=time.dt)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='mute', duration=time.dt)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["noMuteRole"])

        mute = await ctx.db.fetchrow("SELECT objid FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = 'tempmute'", ctx.guild.id, user.id)
        if config.automod.config.muterole not in user.roles and mute is None:
            return ctx.error(lang["notMuted"])

        if config.automod.config.muterole in user.roles:
            await user.remove_roles(config.automod.config.muterole, reason="Unmute")

        if mute is not None:
            await ctx.db.execute("DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 AND type = 'tempmute'", ctx.guild.id, user.id)

        await ctx.embed(lang["unmuteSuccess"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def tempban(self, ctx: Context, user: AdvancedMember, time: FutureTime, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        config = await ctx.cache.get(ctx.guild.id)

        if not self.can_punish_user(ctx, user):
            return await ctx.error(lang["errorPunishNotAllowed"])

        if config is None or config.automod.config.muterole is None:
            return await ctx.error(lang["noMuteRole"])

        timers = self.bot.get_cog('Timers')
        await timers.create_timer(ctx, date=time.dt, objectID=user.id, type='tempban')
        await ctx.guild.ban(user=user, reason=reason, delete_message_days=1)

        await ctx.embed(lang["tempbanSuccess"].format(u=str(user), r=reason, d=time.delta), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("tempban", reason, lang, mod=ctx.author, user=user, duration=time.dt)
        user_embed = std.getUserEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType='ban', duration=time.dt)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed, uEmbed=user_embed)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: Context, user: BannedMember, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)
        await ctx.guild.unban(user.user, reason=reason)

        await ctx.embed(lang["unbanSuccess"].format(u=str(user.user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("unban", reason, lang, mod=ctx.author, user=user.user)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed)

    @cmd()
    @checks.isMod(helper=True)
    async def warn(self, ctx: Context, user: discord.Member, points: int, *, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        if not self.can_punish_user(ctx, user):
            return await ctx.error(lang["errorPunishNotAllowed"])

        if points <= 0 or points > 20:
            return await ctx.error(lang["pointsOverflow"])

        await automod.add_points(ctx, points, reason, user=user)
        await ctx.embed(lang["warnSuccess"].format(u=str(user), r=reason, p=str(points)), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    async def points(self, ctx: Context, user: discord.Member):
        lang = await ctx.lang(utils=True)

        if not self.can_punish_user(ctx, user):
            return await ctx.error(lang["errorPunishNotAllowed"])

        points = await self.bot.db.fetchval('SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2', user.id, ctx.guild.id)
        if points is None:
            return await ctx.error(lang["noPointsError"])

        await ctx.embed(lang["pointsSuccess"].format(u=str(user), p=str(points)), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    async def resetPoints(self, ctx: Context, user: discord.Member, reason: ActionReason = None):
        lang = await ctx.lang(utils=True)

        await ctx.bot.db.execute('DELETE FROM automod.users WHERE sid = $1 AND uid = $2', ctx.guild.id, user.id)
        await ctx.embed(lang["pointsReset"].format(u=str(user), r=reason), delete_after=5)
        await ctx.message.delete(delay=5)

        mod_embed = std.cmdEmbed("resetPoints", reason, lang, mod=ctx.author, user=user.user)
        await logs.createLog(ctx, user=user, mEmbed=mod_embed)

    @cmd(aliases=['slow', 'sm'])
    @checks.isMod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(rate=2, per=15, type=commands.BucketType.channel)
    async def slowmode(self, ctx: Context, seconds=0):
        lang = await ctx.lang(utils=True)

        if seconds < 0 or seconds > 21600:
            return await ctx.error(lang["maxSlowmodeError"])
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.message.delete()
        await ctx.embed(lang["slowmodeSuccess"].format(s=str(seconds)), delete_after=5)
        await ctx.message.delete(delay=5)

    @cmd()
    @checks.isMod()
    async def check(self, ctx: Context, user: Union[BannedMember, discord.Member]):
        lang = await ctx.lang(utils=True)

        if not isinstance(user, discord.Member):
            banData = await ctx.bot.db.fetchrow("SELECT * FROM extra.timers WHERE objid = $1 AND sid = $2 AND type = 'tempban'", user.user.id, ctx.guild.id)
            if banData is None:
                return await ctx.embed(lang["checkUserBanned"].format(r=user.reason))
            else:
                timestamp = datetime.datetime.fromtimestamp(banData['time']).strftime('%d. %m. %Y um %H:%M:%S')
                await ctx.embed(lang["checkBanned"].format(d=str(timestamp), r=user.reason))
        else:
            embed = discord.Embed(color=std.normal_color)
            muteData = await ctx.bot.db.fetchrow("SELECT * FROM extra.timers WHERE objid = $1 AND sid = $2 AND type = 'tempmute'", user.id, ctx.guild.id)
            punishments = await ctx.bot.db.fetch("SELECT * FROM automod.users WHERE uid = $1 AND sid = $2", user.id, ctx.guild.id)

            if muteData:
                timestamp = datetime.datetime.utcfromtimestamp(muteData['time']).strftime('%d. %m. %Y um %H:%M:%S')
                embed.description = lang["checkTempmute"].format(d=timestamp, r=muteData.get("reason"))
            elif punishments:
                punishmentList = [f'{pm["reason"]} [{pm["points"]}]' for pm in punishments]
                embed.add_field(name=lang["checkPunishments"].format(p=str(len(punishmentList))), value='\n'.join(punishmentList))
            else:
                return await ctx.embed(lang["checkNoPunishments"])
            await ctx.send(embed=embed)

    @grp(aliases=['purge'])
    @checks.isMod(helper=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def remove(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), "remove")

    @staticmethod
    async def do_removal(ctx, limit, predicate, lang, *, before=None, after=None):
        if limit > 2000 or limit < 1:
            return await ctx.error(lang['errorClearAmount'])

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        deleted = len(deleted)

        await ctx.embed(lang['clearDeleted'].format(a=deleted - 1), delete_after=5)

    @remove.command()
    async def embeds(self, ctx, amount):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.embeds), lang)

    @remove.command()
    async def files(self, ctx, amount):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.attachments), lang)

    @remove.command()
    async def images(self, ctx, amount):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: len(m.embeds) or len(m.attachments), lang)

    @remove.command(name='all')
    async def _remove_all(self, ctx, amount):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: True, lang)

    @remove.command()
    async def user(self, ctx, amount, user: discord.Member):
        lang = await ctx.lang(utils=True)
        await self.do_removal(ctx, amount, lambda m: m.author == user, lang)

    @remove.command()
    async def contains(self, ctx, amount, *, string: str):
        lang = await ctx.lang(utils=True)
        if len(string) < 3:
            return await ctx.send(lang["minStringLength"])
        await self.do_removal(ctx, amount, lambda m: string in m.content, lang)

    @remove.command(name='bot', aliases=['bots'])
    async def _bot(self, ctx, amount, prefix = None):
        lang = await ctx.lang(utils=True)
        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await self.do_removal(ctx, amount, predicate, lang)

    @remove.command(name='emoji', aliases=['emojis'])
    async def _emoji(self, ctx, amount):
        lang = await ctx.lang(utils=True)
        custom_emoji = re.compile(r'<a?:[a-zA-Z0-9_]+:([0-9]+)>')

        await self.do_removal(ctx, amount, lambda m: custom_emoji.search(m.content), lang)

    @remove.command(name='reactions')
    async def _reactions(self, ctx, search=100):
        lang = await ctx.lang(utils=True)
        if search > 2000:
            return await ctx.error(lang['errorClearAmount'])

        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.embed(lang['removeReaction'].format(a=total_reactions), delete_after=5)

    @remove.command()
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
        await self.do_removal(ctx, args.search, predicate, lang, before=args.before, after=args.after)


def setup(bot):
    bot.add_cog(Moderation(bot))
