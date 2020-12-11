import discord
import logging
from utils.ext.context import Context


logger = logging.getLogger(__name__)


async def createCmdLog(ctx, embed, file=None):
    data = await ctx.cache.get(ctx.guild.id)
    config = data.automod.config

    if data.modules.logging and config.logchannel is not None:
        if ctx.me.permissions_in(config.logchannel).send_messages:
            if file is not None:
                await config.logchannel.send(embed=embed, file=file)
            else:
                await config.logchannel.send(embed=embed)


async def createLog(ctx: Context, *, user: discord.Member = None, mEmbed=None, uEmbed=None, automod=False):
    data = await ctx.cache.get(ctx.guild.id)
    config = data.automod.config

    if data.modules.logging or automod:
        if config.logchannel is not None and mEmbed is not None:
            if ctx.me.permissions_in(config.logchannel).send_messages:
                await config.logchannel.send(embed=mEmbed)

    if user is None:
        return

    if not isinstance(user, discord.Member):
        return

    if config.gmm or automod:
        if uEmbed is not None:
            if not ctx.guild.me.guild_permissions.is_superset(user.guild_permissions):
                return

            try:
                await user.send(embed=uEmbed)
            except (discord.Forbidden, discord.HTTPException):
                return
