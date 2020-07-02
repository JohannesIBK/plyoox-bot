import argparse
import asyncio
import datetime
import io
import re
import shlex
import time
import main

import discord
from discord.ext import commands, tasks

from others import logs
from utils import automod
from utils.ext import checks, standards
from utils.ext.cmds import cmd


class TimeToLong(Exception):
    pass


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


def can_execute_action(ctx, user, target):
    return user.id == ctx.bot.owner_id or \
           user == ctx.guild.owner or \
           user.top_role > target.top_role


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = f'{ctx.author} (ID: {ctx.author.id}): {argument}'

        if len(ret) > 512:
            reason_max = 512 - len(ret) - len(argument)
            raise commands.BadArgument(f'reason is too long ({len(argument)}/{reason_max})')

        return ret


class ParseTime():
    @staticmethod
    def parse(timeStr: str):
        if timeStr.endswith(('j', 'y')):
            try:
                years = int(timeStr.replace('j', '').replace('y', ''))
                if 3 < years <= 1:
                    raise TimeToLong()

                return years * 3600 * 24 * 365 + time.time()
            except:
                raise TypeError

        if timeStr.endswith('d'):
            try:
                days = int(timeStr.replace('d', ''))
                if 365 < days <= 1:
                    raise TimeToLong()

                return days * 3600 * 24 + time.time()
            except:
                raise TypeError

        if timeStr.endswith('h'):
            try:
                hours = float(timeStr.replace('h', ''))
                if 720 < hours <= 0.25:
                    raise TimeToLong()

                return hours * 3600 + time.time()
            except:
                raise TypeError

        else:
            return None


class Moderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.checkTimer.start()

    @tasks.loop(minutes=15)
    async def checkTimer(self):
        punishments = await self.bot.db.fetch('SELECT * FROM automod.punishments WHERE time - extract(EPOCH FROM now()) <= 900;')

        for punishment in punishments:
            unbanTime = punishment['time']
            memberID = punishment['userid']
            guildID = punishment['sid']
            punishmentType = punishment['type']
            self.bot.loop.create_task(self.timer(unbanTime, memberID, guildID, punishmentType))

    @checkTimer.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    async def timer(self, unbanTime: int, memberID: int, guildID: int, punishmentType: str):
        """
        :param unbanTime: UNIX Timestamp when user's punishment runs out
        :param memberID: ID of Member
        :param guildID: ID of Guild
        :param punishmentType: Type of punishment
        :return
        """

        untilUnban = unbanTime - time.time()
        if unbanTime > 0:
            untilUnban = 0

        await asyncio.sleep(untilUnban)

        guild = self.bot.get_guild(guildID)
        self.bot.dispatch('punishment_runout', guild, memberID, punishmentType)

    async def punishUser(self, user: discord.Member):
        if user.guild_permissions.manage_guild:
            return True

        modRoles: list = await self.bot.db.fetchval('SELECT modroles FROM automod.config WHERE sid = $1', user.guild.id)
        if not modRoles:
            return True

        userRoles = [role.id for role in user.roles]
        if any(role_u in modRoles for role_u in userRoles):
            return False

        return True

    # --------------------------------commands--------------------------------

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int, *, reason = 'No Reason'):
        await ctx.message.delete()
        deleted: int = len(await ctx.channel.purge(limit=amount))

        embed = standards.getBaseModEmbed(reason, mod=ctx.author)
        embed.title = 'Moderation [CLEAR]'
        embed.add_field(name=f'{standards.bughunter_badge} **Menge**',
                        value=str(amount))

        await logs.createCmdLog(ctx, embed)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} {deleted} Nachrichten wurden gelöscht.'),
                       delete_after=5)

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def ban(self, ctx, user: discord.Member, *, reason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst diesen User nicht bannen.'))

        if user == ctx.author:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = standards.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [BAN]'
        userEmbed = standards.getUserEmbed(reason, ctx.guild.name, isBan=True)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.ban(reason=reason, delete_message_days=1)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gebannt.'),
                       delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(kick_members=True)
    @checks.isMod()
    async def kick(self, ctx, user: discord.Member, *, reason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst diesen User nicht kicken.'))

        if user == ctx.author:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = standards.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [KICK]'
        userEmbed = standards.getUserEmbed(reason, ctx.guild.name)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.kick(reason=reason)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gekickt.'),
                       delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def softban(self, ctx, user: discord.Member, *, reason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst diesen User nicht kicken.'))

        if user == ctx.author:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = standards.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [SOFTBAN]'
        userEmbed = standards.getUserEmbed(reason, ctx.guild.name)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.ban(reason=reason, delete_message_days=1)
        await ctx.guild.unban(user)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gekickt.'),
                       delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def tempban(self, ctx, user: discord.Member, duration: str, *, reason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst diesen User nicht bannen.'))

        if user == ctx.author:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        if not duration.endswith(('d', 'min', 'h', 'y', 'j')):
            return await ctx.send(embed=standards.getErrorEmbed('Die Dauer wurde falsch angegeben.'))

        unixTime = ParseTime().parse(duration)
        if unixTime is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Bot konnte die Zeit nicht parsen. Bitte versuche es erneut.'))

        embed = standards.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = f'Moderation [TEMPBAN]'
        embed.add_field(name=f'{standards.date_emoji} **__Dauer__**',
                        value=duration)
        userEmbed = standards.getUserEmbed(reason, ctx.guild.name, isBan=True, duration=duration)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.ban(reason=reason, delete_message_days=1)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Der User `{user}` wurde erfolgreich `{duration}` für `{reason}` gebannt.'),
                       delete_after=5)
        await ctx.db.execute('INSERT INTO automod.punishments (sid, userid, type, time) VALUES ($1, $2, $3, $4)',
                             ctx.guild.id, user.id, True, unixTime)
        await ctx.message.delete()

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(self, ctx, user: discord.Member, duration: str, *, reason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst diesen User nicht muten.'))

        muteRoleID = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', ctx.guild.id)
        muteRole = ctx.guild.get_role(muteRoleID)

        if muteRole is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Server hat keine Muterolle.'))

        if user == ctx.author:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        if not duration.endswith(('d', 'min', 'h', 'y', 'j')):
            return await ctx.send(embed=standards.getErrorEmbed('Die Dauer wurde falsch angegeben.'))

        unixTime = ParseTime().parse(duration)
        if unixTime is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Bot konnte die Zeit nicht parsen. Bitte versuche es erneut.'))

        embed = standards.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = f'Moderation [TEMPMUTE]'
        embed.add_field(name=f'{standards.date_emoji} **__Dauer__**',
                        value=duration)
        userEmbed = standards.getUserEmbed(reason, ctx.guild.name, isBan=True, duration=duration)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.add_roles(muteRole)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Der User `{user}` wurde erfolgreich `{duration}` für `{reason}` gemuted.'),
                       delete_after=5)
        await ctx.db.execute('INSERT INTO automod.punishments (sid, userid, type, time) VALUES ($1, $2, $3, $4)',
                             ctx.guild.id, user.id, False, unixTime)
        await ctx.message.delete()

    @cmd()
    @checks.isMod()
    async def warn(self, ctx, user: discord.Member, points: int, *, reason: str):
        if 0 > points <= 20:
            return await ctx.send(embed=standards.getErrorEmbed('Du kannst nur Punkte von 1-20 hinzufügen.'))
        await automod.add_points(ctx, points, reason, user=user)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Dem User {user.mention} wurden {points} Punkte hinzugefügt.'),
                       delete_after=5)

    @cmd()
    @checks.isMod()
    async def points(self, ctx, user: discord.Member):
        userData = await self.bot.db.fetchval('SELECT points FROM automod.users WHERE key = $1', f'{user.id}{ctx.guild.id}')
        if userData is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der User hat noch nie etwas getan.'))

        await ctx.send(embed=discord.Embed(description=f'Der User hat {userData} Punkte.'))

    @cmd()
    @commands.guild_only()
    @checks.isAdmin()
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx, *, args):
        # QUELLE: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py#L733

        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--channel', '-c', default=ctx.channel)
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
            return await ctx.send(str(e))

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
                    return await ctx.send(embed=standards.getErrorEmbed(f'Regex Fehler: {e}'))
                else:
                    predicates.append(lambda m, x = _match: x.match(m.content))
            if args.embeds:
                predicates.append(args.embeds)
            if args.files:
                predicates.append(args.files)

            async for message in channel.history(limit=min(max(1, args.search), 2000), before=before, after=after):
                if all(p(message) for p in predicates):
                    members.append(message.author)
        else:
            members = ctx.guild.members

        # member filters
        predicates = [
            lambda m: m.id != ctx.author.id,
            lambda m: can_execute_action(ctx, ctx.author, m),  # Only if applicable
            lambda m: not m.bot,  # No bots
            lambda m: m.discriminator != '0000',  # No deleted users
        ]

        async def _resolve_member(member_id):
            r = ctx.guild.get_member(member_id)
            if r is None:
                try:
                    return await ctx.guild.fetch_member(member_id)
                except discord.HTTPException as exc:
                    raise commands.BadArgument(
                        f'User mit der ID `{member_id}` konnte nicht gefunden werden: {exc}') from None
            return r

        if args.regex:
            try:
                _regex = re.compile(args.regex)
            except re.error as e:
                return await ctx.channel.send(embed=standards.getErrorEmbed(f'Regex Fehler: {e}'))
            else:
                predicates.append(lambda m, x = _regex: x.match(m.name))

        if args.no_avatar:
            predicates.append(lambda m: m.avatar is None)
        if args.no_roles:
            predicates.append(lambda m: len(getattr(m, 'roles', [])) <= 1)

        now = datetime.datetime.utcnow()
        if args.created:
            def created(memb, *, offset = now - datetime.timedelta(minutes=args.created)):
                return memb.created_at > offset

            predicates.append(created)
        if args.joined:
            def joined(memb, *, offset = now - datetime.timedelta(minutes=args.joined)):
                return memb.joined_at and memb.joined_at > offset

            predicates.append(joined)
        if args.joined_after:
            _joined_after_member = await _resolve_member(args.joined_after)

            def joined_after(memb, *, _other = _joined_after_member):
                return memb.joined_at and _other.joined_at and memb.joined_at > _other.joined_at

            predicates.append(joined_after)
        if args.joined_before:
            _joined_before_member = await _resolve_member(args.joined_before)

            def joined_before(memb, *, _other = _joined_before_member):
                return memb.joined_at and _other.joined_at and memb.joined_at < _other.joined_at

            predicates.append(joined_before)

        members = {m for m in members if all(p(m) for p in predicates)}
        if len(members) == 0:
            return await ctx.channel.send(embed=standards.getErrorEmbed('Es wurde kein User gefunden, auf den diese Kriterien zutreffen.'))

        if args.show:
            members = sorted(members, key=lambda m: m.joined_at or now)
            fmt = "\n".join(
                '{id}\tBeigetreten: {joined_at}\tErstellt: {created_at}\t{m}'.format(id=m.id, joined_at=m.joined_at,
                                                                                     created_at=m.created_at, m=m) for m
                in members)
            content = f'Useranzahl: {len(members)}\n{fmt}'
            file = discord.File(io.BytesIO(content.encode('utf-8')), filename='members.txt')
            return await ctx.send(file=file)

        if args.reason is None:
            return await ctx.send(embed=standards.getErrorEmbed('Das Argument `--reason` wird benötigt'))
        else:
            reason = await ActionReason().convert(ctx, args.reason)

        confirm = await ctx.prompt(f'Das wird **{len(members)} User bannen**. Sicher?')
        if not confirm:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                      description=f'{standards.error_emoji} Abgebrochen'))

        count = 0
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason)
            except discord.HTTPException:
                pass
            else:
                count += 1

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Es wurden {count}/{len(members)} User gebannt.'))

        embed = standards.getBaseModEmbed(reason, mod=ctx.author)
        embed.title = f'Moderation [MASSBAN]'
        embed.add_field(name=f'{standards.bughunter_badge} **User:** {count}',
                        value=f'**Gebannt:** {count}/{len(members)}')

        await logs.createCmdLog(ctx, embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
