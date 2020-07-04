import time
import discord

from others import logs
from utils.ext import standards, checks, context


async def add_points(ctx: context, addPoints: int, modType: str, user: discord.Member = None):
    await ctx.message.delete()

    if user is not None:
        punishedUser: discord.Member = user
    else:
        punishedUser: discord.Message = ctx.author

    key: str = f'{punishedUser.id}{ctx.guild.id}'
    msg: discord.Message = ctx.message

    userData = await ctx.bot.db.fetchrow(
        'INSERT INTO automod.users (userid, guildid, points, key, time) VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (key) DO UPDATE SET points = users.points + $3, time = $5 RETURNING points, time',
        punishedUser.id, ctx.guild.id, addPoints, key, time.time())

    points: int = userData['points']

    if time.time() - userData['time'] > 604800:
        await ctx.bot.db.execute('UPDATE automod.users SET points = $1, time = $2 WHERE key = $2', addPoints, time.time(), key)
        points: int = addPoints

    data = await ctx.bot.db.fetchrow(
        "SELECT action, max_points, muterole, mute FROM automod.config WHERE sid = $1", ctx.guild.id)

    action: int = data['action']
    maxPoints: int = data['max_points']
    unixTime: float = time.time() + data['mute']

    message: str = msg.content if len(msg.content) < 1015 else f'{ctx.message.content[:1015]}...'

    embed: discord.Embed = standards.getBaseModEmbed(f'{modType} [+{addPoints}]', punishedUser)
    userEmbed: discord.Embed = standards.getBaseModEmbed(f'{modType} [+{addPoints}]')
    userEmbed.add_field(name=f'{standards.folder_emoji} **Server**', value=ctx.guild.name)
    embed.title = f'Automoderation [LOG]'
    userEmbed.title = f'Automoderation [LOG]'
    if user is not None:
        embed.add_field(name=f'{standards.supporter_emoji} **__Moderator__**',
                        value=ctx.author.mention)
    embed.add_field(name=f'{standards.invite_emoji} **__Punkte__**', value=f'{points}/{maxPoints}', inline=False)
    userEmbed.add_field(name=f'{standards.invite_emoji} **__Punkte__**', value=f'{points}/{maxPoints}', inline=False)
    if user is None:
        userEmbed.add_field(name=f'{standards.list_emoji} **__Message__**', value=message, inline=False)
        embed.add_field(name=f'{standards.list_emoji} **__Message__**', value=message, inline=False)

    if points >= maxPoints:
        if action is None:
            embed.title = 'Automoderation [LOG]'

        if action == 1:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                embed.title = 'Automoderation [KICK]'
                await punishedUser.kick(reason="Automoderation: User reached max points.")
                await ctx.bot.db.execute("UPDATE automod.users SET points = 0 WHERE key = $1", key)

        if action == 2:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                embed.title = 'Automoderation [BAN]'
                await punishedUser.ban(reason="Automoderation: User reached max points.")
                await ctx.bot.db.execute("UPDATE automod.users SET points = 0 WHERE key = $1", key)

        if action == 3:
            if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
                embed.title = 'Automoderation [TEMPBAN]'
                await punishedUser.ban(reason="Automoderation: User reached max points.")
                await ctx.db.execute('INSERT INTO automod.punishments (sid, userid, type, time) VALUES ($1, $2, $3, $4)',
                                     ctx.guild.id, punishedUser.id, True, unixTime)

        if action == 4:
            if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
                muteRole = ctx.guild.get_role(data['muterole'])
                if muteRole is None:
                    return
                embed.title = 'Automoderation [TEMPMUTE]'
                await punishedUser.add_roles(muteRole)
                await ctx.db.execute('INSERT INTO automod.punishments (sid, userid, type, time) VALUES ($1, $2, $3, $4)',
                                     ctx.guild.id, punishedUser.id, False, unixTime)

    await logs.createEmbedLog(ctx=ctx, modEmbed=embed, userEmbed=userEmbed, member=punishedUser, ignoreNoLogging=True)
