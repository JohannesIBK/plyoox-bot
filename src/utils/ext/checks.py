import discord
from discord.ext import commands

from utils.ext import context


def isMod(*, helper: bool = False):
    async def predicate(ctx: context.Context):
        perms = ctx.author.permissions_in(ctx.channel)
        if ctx.message.author.id == 263347878150406144 or perms.manage_guild:
            return True

        data = await ctx.cache.get(ctx.guild.id)
        config = data.automod
        if data is None or data.automod is None:
            return
        roles = []
        roles.extend(config.config.modroles)
        if helper:
            roles.extend(config.config.helperroles)

        user_roles = [role.id for role in ctx.author.roles]
        if any(role in roles for role in user_roles):
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
    async def predicate(ctx: context.Context):
        config = await ctx.cache.get(ctx.guild.id)
        if config is None or not config.modules:
            return False
        if modul == 'fun' and config.modules.fun:
            return True
        if modul == 'leveling' and config.modules.leveling:
            return True
        if modul == 'timers' and config.modules.timers:
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


async def ignoresAutomod(ctx: context.Context):
    if not ctx.me.top_role.position > ctx.message.author.top_role.position:
        return True
    if ctx.author.permissions_in(ctx.channel).manage_messages:
        return True

    data = await ctx.cache.get(ctx.guild.id)

    if data is None or data.automod.config is None:
        return False

    roles = []
    roles.extend(data.automod.config.modroles)
    roles.extend(data.automod.config.helperroles)

    author_roles = [role.id for role in ctx.author.roles]
    if any(roleID in roles for roleID in author_roles):
        return True
