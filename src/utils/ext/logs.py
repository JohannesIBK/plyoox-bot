from typing import Union

import discord


async def createCmdLog(ctx, embed, file = None):
    data = await ctx.bot.db.fetchrow("SELECT logchannel, logging FROM automod.config WHERE sid = $1", ctx.guild.id)
    if data is None:
        return

    if data['logging']:
        logchannel = ctx.guild.get_channel(data['logchannel'])

        if logchannel is not None and ctx.me.permissions_in(logchannel).send_messages:
            if file is not None:
                await logchannel.send(embed=embed, file=file)
            else:
                await logchannel.send(embed=embed)

async def createEmbedLog(ctx, modEmbed = None, userEmbed = None, member: Union[discord.Member, discord.User] = None, ignoreNoLogging = False, ignoreMMSG = False):
    data = await ctx.bot.db.fetchrow("SELECT gmm, logchannel, logging FROM automod.config WHERE sid = $1", ctx.guild.id)
    if data is None:
        return

    if (data['logging'] or ignoreNoLogging) and modEmbed is not None:
        logchannel = ctx.guild.get_channel(data['logchannel'])
        if logchannel is not None:
            if ctx.me.permissions_in(logchannel).send_messages:
                await logchannel.send(embed=modEmbed)

        if ignoreMMSG:
            try:
                return await member.send(embed=userEmbed)
            except discord.Forbidden:
                return

    if not isinstance(member, discord.Member):
        return

    if data['gmm'] and member is not None and userEmbed is not None:
        if not ctx.guild.me.guild_permissions.is_superset(member.guild_permissions):
            return

        try:
            return await member.send(embed=userEmbed)
        except discord.Forbidden:
            return
