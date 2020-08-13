import discord
from discord.ext import commands

from utils.ext import context


def isMod(*, helper: bool = False):
    async def predicate(ctx):
        perms = ctx.author.permissions_in(ctx.channel)
        if ctx.message.author.id == 263347878150406144 or perms.manage_guild:
            return True

        if helper:
            data = await ctx.bot.db.fetchrow('SELECT modroles, helperroles FROM automod.config WHERE sid = $1', ctx.guild.id)
            if data is None:
                return
            roles = []
            if data['modroles'] is not None:
                roles.extend(data['modroles'])
            if data['helperroles'] is not None:
                roles.extend(data['helperroles'])
        else:
            roles = await ctx.bot.db.fetchval('SELECT modroles FROM automod.config WHERE sid = $1', ctx.guild.id)
        if not roles:
            if helper:
                raise commands.MissingPermissions(['Du musst ein Moderator oder Helfer sein, um den Command auszuführen'])
            raise commands.MissingPermissions(['Du musst ein Moderator sein, um den Command auszuführen'])

        userRoles = [role.id for role in ctx.author.roles]
        if any(role in roles for role in userRoles):
            return True
        else:
            if helper:
                raise commands.MissingPermissions(['Du musst ein Moderator oder Helfer sein, um den Command auszuführen'])
            raise commands.MissingPermissions(['Du musst ein Moderator sein, um den Command auszuführen'])

    return commands.check(predicate)


def isAdmin():
    async def predicate(ctx):
        user = ctx.author
        if user.id == ctx.bot.owner_id or user.guild_permissions.administrator:
            return True
        else:
            raise commands.MissingPermissions(['administrator'])

    return commands.check(predicate)


def hasPerms(**perms):
    async def predicate(ctx):
        if ctx.message.author.id == 263347878150406144:
            return True

        permissions = ctx.channel.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing:
            return True
        raise commands.MissingPermissions(missing)

    return commands.check(predicate)


def isBriiaan():
    async def predicate(ctx):
        return ctx.guild.id == 665609018793787422

    return commands.check(predicate)


def isActive(modul):
    async def predicate(ctx):
        status = await ctx.db.fetchrow(
            "SELECT fun, leveling, timers FROM config.modules WHERE sid = $1", ctx.guild.id)
        modul_bool = status[modul]
        if modul_bool:
            return True
        else:
            raise commands.DisabledCommand

    return commands.check(predicate)


def hasPermsByName(ctx, member, permsSearch):
    if not isinstance(member, discord.Member):
        return False

    perms = [perm for perm, value in member.permissions_in(ctx.channel) if value]
    if permsSearch.lower() in perms:
        return True


async def ignores_automod(ctx: context):
    if not ctx.me.top_role.position > ctx.message.author.top_role.position:
        return True
    if ctx.author.permissions_in(ctx.channel).manage_messages:
        return True

    data = await ctx.db.fetchrow('SELECT modroles, ignoredroles FROM automod.config WHERE sid = $1', ctx.guild.id)
    if data is None:
        return False

    roles = []
    if data['ignoredroles'] is not None:
        roles.extend(data['ignoredroles'])

    if data['modroles'] is not None:
        roles.extend(data['modroles'] )

    authorRoles = [role.id for role in ctx.author.roles]
    if any(roleID in roles for roleID in authorRoles):
        return True
