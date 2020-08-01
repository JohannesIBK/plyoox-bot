import argparse
import datetime
import io
import re
import shlex
import time
from typing import Union

import discord
from discord.ext import commands, tasks

import main
from others import logs
from utils import automod
from utils.automod import automod, add_points
from utils.ext import checks, standards as std, context, converters
from utils.ext.cmds import cmd


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
            raise commands.BadArgument(f'Grund zu lang ({len(argument)}/{reason_max})')

        return ret


class Moderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.checkPunishments.start()

    @tasks.loop(minutes=30)
    async def checkPunishments(self):
        await self.bot.db.execute('DELETE FROM automod.users WHERE $1 - time >= 2592000', time.time())

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not isinstance(msg.author, discord.Member):
            return

        ctx = await self.bot.get_context(msg, cls=context.Context)
        await automod(ctx)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
        await self.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", user.id, guild.id)

    @commands.Cog.listener()
    async   def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return

        if not isinstance(before.author, discord.Member):
            return

        if not before.created_at or not after.edited_at:
            return

        if before.content == after.content:
            return

        ctx = await self.bot.get_context(after, cls=context.Context)
        await automod(ctx)

        if (after.edited_at - before.created_at).seconds <= 30:
            await self.bot.process_commands(after)

    async def punishUser(self, user: Union[discord.Member, discord.User]):
        if user.id == self.bot.user.id:
            return False

        if not isinstance(user, discord.Member):
            return True

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
    async def clear(self, ctx, amount: int, *, reason: ActionReason = 'No Reason'):
        if amount > 2000:
            return await ctx.send(embed=std.getErrorEmbed('Es können nicht mehr wie 2000 Nachrichten gelöscht werden.'))

        messages = await ctx.channel.history(limit=amount + 1).flatten()
        content = '\n'.join(f'{msg.author} ({msg.author.id}): {msg.content}' for msg in messages)
        file = io.BytesIO(content.encode())

        deleted: int = len(await ctx.channel.purge(limit=amount + 1))

        embed = std.getBaseModEmbed(reason, mod=ctx.author)
        embed.title = 'Moderation [CLEAR]'
        embed.add_field(name=f'{std.bughunter_badge} **Menge**',
                        value=str(deleted - 1))
        embed.add_field(name=f'{std.channel_emoji} **Channel**',
                        value=ctx.channel.mention)


        await logs.createCmdLog(ctx, embed, file=file)
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} {deleted - 1} Nachrichten wurden gelöscht.'), delete_after=5)

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def ban(self, ctx, user: Union[discord.Member, discord.User], *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht bannen.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [BAN]'
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=0)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await ctx.guild.ban(user, reason=reason, delete_message_days=1)
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gebannt.'),
                       delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(kick_members=True)
    @checks.isMod()
    async def kick(self, ctx, user: discord.Member, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht kicken.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [KICK]'
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=1)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.kick(reason=reason)
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gekickt.'),
                       delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def softban(self, ctx, user: discord.Member, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht kicken.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = 'Moderation [SOFTBAN]'
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=1)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await ctx.guild.ban(user, reason=reason, delete_message_days=1)
        await ctx.guild.unban(user)
        await ctx.send(embed=std.getEmbed('{std.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gekickt.'), delete_after=5)
        await ctx.message.delete()

    @cmd()
    @commands.bot_has_permissions(ban_members=True)
    @checks.isMod()
    async def tempban(self, ctx, user: discord.Member, duration: converters.ParseTime, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht bannen.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = f'Moderation [TEMPBAN]'
        embed.add_field(name=f'{std.date_emoji} **__Dauer__**',
                        value=duration)
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=0, duration=duration)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.ban(reason=reason, delete_message_days=1)
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Der User `{user}` wurde erfolgreich `{duration}` für `{reason}` gebannt.'), delete_after=5)
        await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time) VALUES ($1, $2, 0, $3)',
                             ctx.guild.id, user.id, duration)
        await ctx.message.delete()

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(self, ctx, user: discord.Member, duration: converters.ParseTime, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht muten.'))

        muteRoleID = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', ctx.guild.id)
        muteRole = ctx.guild.get_role(muteRoleID)
        if muteRole is None:
            return await ctx.send(embed=std.getErrorEmbed('Der Server hat keine Muterolle.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = f'Moderation [TEMPMUTE]'
        embed.add_field(name=f'{std.date_emoji} **__Dauer__**', value=duration)
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=2, duration=duration)

        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)
        await user.add_roles(muteRole)
        await ctx.send(embed=std.getEmbed('{std.law_emoji} Der User `{user}` wurde erfolgreich `{duration}` für `{reason}` gemuted.'),
                       delete_after=5)
        await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time) VALUES ($1, $2, 1, $3)',
                             ctx.guild.id, user.id, duration)
        await ctx.message.delete()

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, user: discord.Member, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht muten.'))

        muteRoleID = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', ctx.guild.id)
        muteRole = ctx.guild.get_role(muteRoleID)
        if muteRole is None:
            return await ctx.send(embed=std.getErrorEmbed('Der Server hat keine Muterolle.'))

        if user == ctx.author:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst den Command nicht an dir selbst ausführen.'))

        await user.add_roles(muteRole)
        await ctx.message.delete()
        embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
        embed.title = f'Moderation [MUTE]'
        embed.add_field(name=f'{std.date_emoji} **__Dauer__**', value='Permanent')
        userEmbed = std.getUserEmbed(reason, ctx.guild.name, punishType=2)
        await logs.createEmbedLog(ctx, modEmbed=embed, userEmbed=userEmbed, member=user)

        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Der User `{user}` wurde erfolgreich für `{reason}` gemuted.'), delete_after=5)

    @cmd()
    @checks.isMod()
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, user: discord.Member, *, reason: ActionReason = 'No Reason'):
        muteRoleID = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', ctx.guild.id)
        muteRole = ctx.guild.get_role(muteRoleID)
        if muteRole is None:
            return await ctx.send(embed=std.getErrorEmbed('Der Server hat keine Muterolle.'))

        if muteRole in user.roles:
            await user.remove_roles(muteRole, reason=reason)
            await ctx.send(embed=std.getEmbed('Der User wurde erfolgreich entmutet.'))

            await ctx.message.delete()
            embed = std.getBaseModEmbed(reason, user=user, mod=ctx.author)
            embed.title = f'Moderation [UNMUTE]'
            await logs.createEmbedLog(ctx, modEmbed=embed, member=user)
        else:
            return await ctx.send(embed=std.getEmbed('Der User ist nicht gemutet.'))

        await self.bot.db.execute("DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = 1", ctx.guild.id, user.id)

    @cmd()
    @checks.isMod()
    async def warn(self, ctx, user: discord.Member, points: int, *, reason: ActionReason = 'No Reason'):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesen User nicht warnen.'))

        if points < 0 or points > 20:
            return await ctx.send(embed=std.getErrorEmbed('Du kannst nur Punkte von 1-20 hinzufügen.'))
        await add_points(ctx, points, reason, user=user)
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Dem User {user.mention} wurden {points} Punkte hinzugefügt.'), delete_after=5)

    @cmd()
    @checks.isMod()
    async def points(self, ctx, user: discord.Member):
        if not await self.punishUser(user):
            return await ctx.send(embed=std.getErrorEmbed('Du kannst diesem User keine Punkte geben.'))

        points = await self.bot.db.fetchval('SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2', user.id, ctx.guild.id)
        if points is None:
            return await ctx.send(embed=std.getErrorEmbed('Der User hat noch nie etwas getan.'))

        await ctx.send(embed=std.getEmbed(f'Der User hat {points} Punkte.'))

    @cmd()
    @checks.isMod()
    async def resetPoints(self, ctx, user: discord.Member):
        await ctx.bot.db.execute('DELETE FROM automod.users WHERE sid = $1 AND uid = $2', ctx.guild.id, user.id)
        await ctx.message.delete()
        await ctx.send(embed=std.getEmbed('Die Punkte des Users wurden zurückgesetzt.'), delete_after=5)

    @cmd(aliases=['slow', 'sm'])
    @checks.isMod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(rate=2, per=15, type=commands.BucketType.channel)
    async def slowmode(self, ctx, seconds = 0):
        if seconds < 0 or seconds > 21600:
            return await ctx.send(embed=std.getErrorEmbed('Die Sekundenanzahl muss zwischen 0 und 21600 (6h) liegen'))
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.message.delete()
        await ctx.send(embed=std.getEmbed(f'Der Slowmode wurde erfolgreich auf `{seconds}` {"Sekunde" if seconds == 1 else "Sekunden"} gesetzt.'), delete_after=5)

    @cmd()
    @commands.guild_only()
    @checks.isAdmin()
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx, *, args):
        # QUELLE: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py#L733

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
                    return await ctx.send(embed=std.getErrorEmbed(f'Regex Fehler: {e}'))
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
                    raise commands.BadArgument(f'User mit der ID `{member_id}` konnte nicht gefunden werden: {exc}') from None
            return r

        if args.regex:
            try:
                _regex = re.compile(args.regex)
            except re.error as e:
                return await ctx.channel.send(embed=std.getErrorEmbed(f'Regex Fehler: {e}'))
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
            return await ctx.channel.send(embed=std.getErrorEmbed('Es wurde kein User gefunden, auf den diese Kriterien zutreffen.'))

        if args.show:
            members = sorted(members, key=lambda m: m.joined_at or now)
            fmt = "\n".join('{id}\tBeigetreten: {joined_at}\tErstellt: {created_at}\t{m}'
                            .format(id=m.id, joined_at=m.joined_at, created_at=m.created_at, m=m) for m in members)
            content = f'Useranzahl: {len(members)}\n{fmt}'
            file = discord.File(io.BytesIO(content.encode('utf-8')), filename='members.txt')
            return await ctx.send(file=file)

        if args.reason is None:
            return await ctx.send(embed=std.getErrorEmbed('Das Argument `--reason` wird benötigt'))
        else:
            reason = await ActionReason().convert(ctx, args.reason)

        confirm = await ctx.prompt(f'Das wird **{len(members)} User bannen**. Sicher?')
        if not confirm:
            return await ctx.send(embed=std.getEmbed(f'{std.error_emoji} Abgebrochen'))

        count = 0
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason)
            except discord.HTTPException:
                pass
            else:
                count += 1

        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Es wurden {count}/{len(members)} User gebannt.'))

        embed = std.getBaseModEmbed(reason, mod=ctx.author)
        embed.title = f'Moderation [MASSBAN]'
        embed.add_field(name=f'{std.bughunter_badge} **User:** {count}', value=f'**Gebannt:** {count}/{len(members)}')

        await logs.createCmdLog(ctx, embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
