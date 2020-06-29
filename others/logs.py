import discord


async def createCmdLog(ctx, embed):
    data = await ctx.bot.db.fetchrow("SELECT logchannel, logging FROM automod.config WHERE sid = $1", ctx.guild.id)
    logchannelID = data['logchannel']
    logging = data['logging']

    if logging:
        logchannel = ctx.guild.get_channel(logchannelID)

        if logchannel is not None:
            await logchannel.send(embed=embed)


async def createEmbedLog(ctx, modEmbed = None, userEmbed = None,
                         member: discord.Member = None, ignoreNoLogging: bool = False):
    data = await ctx.bot.db.fetchrow("SELECT gmm, logchannel, logging FROM automod.config WHERE sid = $1", ctx.guild.id)

    userLog = data['gmm']
    logchannelID = data['logchannel']
    logging = data['logging']

    if (logging or ignoreNoLogging) and modEmbed is not None:
        logchannel = ctx.guild.get_channel(logchannelID)

        if logchannel is not None:
            if ctx.me.permissions_in(logchannel).send_messages:
                await logchannel.send(embed=modEmbed)

        if ignoreNoLogging:
            try:
                await member.send(embed=userEmbed)
            except discord.Forbidden:
                pass

    if userLog and member is not None and userEmbed is not None:
        if not ctx.guild.me.guild_permissions.is_superset(member.guild_permissions):
            return

        try:
            await member.send(embed=userEmbed)
        except discord.Forbidden:
            pass
