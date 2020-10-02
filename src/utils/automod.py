import datetime
import json
import re
import time

import discord

from main import Plyoox
from utils.ext import standards as std, checks, context, logs

DISCORD_INVITE = '(discord(app\.com\/invite|\.com(\/invite)?|\.gg)\/?[a-zA-Z0-9-]{2,32})'
EXTERNAL_LINK = '((https?:\/\/(www\.)?|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})'
EVERYONE_MENTION = '@(here|everyone)'
discordRegex = re.compile(DISCORD_INVITE, re.IGNORECASE)
linkRegex = re.compile(EXTERNAL_LINK, re.IGNORECASE)
everyoneRegex = re.compile(EVERYONE_MENTION)


def findWord(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search


async def managePunishment(ctx, punishment, reason):
    await ctx.message.delete()
    config = await ctx.bot.cache.get(ctx.guild.id)
    if not config.automod:
        return
    config = config.automod.config

    user: discord.Member = ctx.author
    msg = ctx.message.content if len(ctx.message.content) < 1015 else f'{ctx.message.content[:1015]}...'
    reason = f'Automoderation: {reason}'

    embed: discord.Embed = std.getBaseModEmbed(reason, ctx.author, ctx.me)
    userEmbed: discord.Embed = std.getBaseModEmbed(reason)
    userEmbed.add_field(name=f'{std.folder_emoji} **Server**', value=ctx.guild.name, inline=False)
    userEmbed.add_field(name=f'{std.list_emoji} **__Message__**', value=msg, inline=False)
    embed.add_field(name=f'{std.channel_emoji} **__Channel__**', value=ctx.channel.mention, inline=False)
    embed.add_field(name=f'{std.list_emoji} **__Message__**', value=msg, inline=False)

    if punishment == 1:
        if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
            embed.title = 'AUTOMODERATION [KICK]'
            userEmbed.title = 'AUTOMODERATION [KICK]'
            await ctx.guild.kick(user, reason=reason)
    elif punishment == 2:
        if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
            embed.title = 'AUTOMODERATION [BAN]'
            userEmbed.title = 'AUTOMODERATION [BAN]'
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 3:
        if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
            embed.title = 'AUTOMODERATION [TEMPBAN]'
            userEmbed.title = 'AUTOMODERATION [TEMPBAN]'
            unixTime = time.time() + config.bantime
            embed.add_field(name=f'{std.date_emoji} **__Entbann__**', value=datetime.datetime.fromtimestamp(unixTime).strftime('%d. %m. %Y um %H:%M:%S'))
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, 0, unixTime, json.dumps({'reason': reason}))
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 4:
        if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
            if config.muterole is None:
                return

            embed.title = 'AUTOMODERATION [TEMPMUTE]'
            userEmbed.title = 'AUTOMODERATION [TEMPMUTE]'
            unixTime = time.time() + config.mutetime
            embed.add_field(name=f'{std.date_emoji} **__Entmute__**', value=datetime.datetime.fromtimestamp(unixTime).strftime('%d. %m. %Y um %H:%M:%S'))
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, 1, unixTime, json.dumps({'reason': reason}))
            await user.add_roles(config.muterole, reason=reason)

    await logs.createEmbedLog(ctx=ctx, modEmbed=embed, userEmbed=userEmbed, member=user, ignoreMMSG=True, ignoreNoLogging=True)


async def add_points(ctx: context, addPoints, modType, user: discord.Member = None):
    await ctx.message.delete()
    config = await ctx.bot.cache.get(ctx.guild.id)
    if not config.automod:
        return
    config = config.automod.config

    if user is not None:
        punishedUser: discord.Member = user
    else:
        punishedUser: discord.Message = ctx.author

    await ctx.bot.db.execute(
        'INSERT INTO automod.users (uid, sid, points, time, reason) VALUES ($1, $2, $3, $4, $5)',
        punishedUser.id, ctx.guild.id, addPoints, time.time(), f'Automoderation: {modType}')

    points  = await ctx.bot.db.fetchval('SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2 AND $3 - time < 2592000', punishedUser.id, ctx.guild.id, time.time())
    msg: discord.Message = ctx.message

    action = config.action
    maxPoints = config.maxpoints
    unixTimeMute = unixTimeBan = time.time() + 86400

    if config.mutetime:
        unixTimeMute: float = time.time() + config.mutetime
    if config.bantime:
        unixTimeBan: float = time.time() + config.bantime

    message = msg.content if len(msg.content) < 1015 else f'{ctx.message.content[:1015]}...'

    embed: discord.Embed = std.getBaseModEmbed(f'{modType} [+{addPoints}]', punishedUser)
    userEmbed: discord.Embed = std.getBaseModEmbed(f'{modType} [+{addPoints}]')
    userEmbed.add_field(name=f'{std.folder_emoji} **Server**', value=ctx.guild.name)
    embed.title = f'AUTOMODERATION [LOG]'
    userEmbed.title = f'AUTOMODERATION [LOG]'
    if user is not None:
        embed.add_field(name=f'{std.supporter_emoji} **__Moderator__**', value=ctx.author.mention, inline=False)
    embed.add_field(name=f'{std.channel_emoji} **__Channel__**', value=ctx.channel.mention, inline=False)
    embed.add_field(name=f'{std.invite_emoji} **__Punkte__**', value=f'{points}/{maxPoints}', inline=False)
    userEmbed.add_field(name=f'{std.invite_emoji} **__Punkte__**', value=f'{points}/{maxPoints}', inline=False)
    if user is None:
        userEmbed.add_field(name=f'{std.list_emoji} **__Message__**', value=message, inline=False)
        embed.add_field(name=f'{std.list_emoji} **__Message__**', value=message, inline=False)

    if points >= maxPoints:
        if action is None:
            embed.title = 'AUTOMODERATION [LOG]'

        if action == 1:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                embed.title = 'AUTOMODERATION [KICK]'
                await punishedUser.kick(reason="Automoderation")
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, msg.guild.id)
            else:
                return

        if action == 2:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                embed.title = 'AUTOMODERATION [BAN]'
                await punishedUser.ban(reason="Automoderation")
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, msg.guild.id)
            else:
                return

        if action == 3:
            if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
                embed.add_field(name=f'{std.date_emoji} **__Entbann__**', value=datetime.datetime.fromtimestamp(unixTimeBan).strftime('%d. %m. %Y um %H:%M:%S'))
                embed.title = 'AUTOMODERATION [TEMPBAN]'
                await punishedUser.ban(reason="Automoderation: Punktesystem")
                await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                     ctx.guild.id, punishedUser.id, 0, unixTimeBan, json.dumps({'reason': 'Automoderation: Punktesystem'}))
            else:
                return
        if action == 4:
            if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
                if config.muterole is None:
                    return

                embed.add_field(name=f'{std.date_emoji} **__Entmute__**', value=datetime.datetime.fromtimestamp(unixTimeMute).strftime('%d. %m. %Y um %H:%M:%S'))
                embed.title = 'AUTOMODERATION [TEMPMUTE]'
                await punishedUser.add_roles(config.muterole, reason='Automoderation')
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, msg.guild.id)
                await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                     ctx.guild.id, punishedUser.id, 1, unixTimeMute, json.dumps({'reason': 'Automoderation: Punktesystem'}))
            else:
                return
    await logs.createEmbedLog(ctx=ctx, modEmbed=embed, userEmbed=userEmbed, member=punishedUser, ignoreNoLogging=True, ignoreMMSG=True)


async def automod(ctx):
    bot: Plyoox = ctx.bot
    guild: discord.Guild = ctx.guild
    msg: discord.Message = ctx.message
    channel: discord.TextChannel = ctx.channel
    config = await bot.cache.get(ctx.guild.id)
    modules =  config.modules
    automod = config.automod

    if not modules.automod or not config.automod:
        return

    if automod.blacklist.state:
        blacklist = automod.blacklist
        for word in blacklist.words:
            if findWord(word)(msg.content.lower()):
                if not await checks.ignores_automod(ctx):

                    if channel.id in blacklist.whitelist:
                        return

                    if blacklist.state == 5:
                        return await add_points(ctx, blacklist.points, 'Blacklisted Word')
                    else:
                        return await managePunishment(ctx, blacklist.state, 'Blacklisted Word')

    if discordRegex.findall(msg.content):
        invites = automod.invites
        if await checks.ignores_automod(ctx):
            return

        if not invites.state:
            return

        if channel.id in invites.whitelist:
            return

        whitelistedServers = [guild.id]
        whitelistedServers.extend([int(guildID) for guildID in invites.partner])

        hasInvite: bool = False
        for invite in discordRegex.findall(msg.content):
            try:
                invite = await bot.fetch_invite(invite[0])
            except discord.NotFound:
                continue

            except discord.Forbidden:
                if invites.state == 5:
                    return await add_points(ctx, invites.points, 'Invite')
                else:
                    return await managePunishment(ctx, invites.state, 'Invite')

            if invite.guild.id not in whitelistedServers:
                hasInvite = True
                break

        if hasInvite:
            if invites.state == 5:
                return await add_points(ctx, invites.points, 'Invite')
            else:
                return await managePunishment(ctx, invites.state, 'Invite')


    elif linkRegex.findall(msg.content):
        links = automod.links
        if await checks.ignores_automod(ctx):
            return

        if not links.state:
            return

        if channel.id in links.whitelist:
            return

        linksList = ['discord.gg', 'discord.com', 'discordapp.com', 'plyoox.net']
        linksList.extend(links.links)

        linksObj = linkRegex.findall(msg.content)
        for linkObj in linksObj:
            link = linkObj[0].replace(linkObj[1], '')
            if links.iswhitelist:
                if link not in linksList:
                    if links.state == 5:
                        return await add_points(ctx, links.points, 'Link')
                    else:
                        return await managePunishment(ctx, links.state, 'Link')
            else:
                if link in links:
                    if links.state == 5:
                        return await add_points(ctx, links.points, 'Link')
                    else:
                        return await managePunishment(ctx, links.state, 'Link')


    if not msg.clean_content.islower() and len(msg.content) > 15:
        caps = automod.caps
        if await checks.ignores_automod(ctx):
            return

        lenCaps = len(re.findall(r'[A-ZÄÖÜ]', msg.clean_content))
        percent = lenCaps / len(msg.content)
        if percent > 0.7:
            if not caps.state:
                return

            if channel.id in caps.whitelist:
                return

            if caps.state == 5:
                return await add_points(ctx, caps.points, 'Caps')
            else:
                return await managePunishment(ctx, caps.state, 'Caps')

    if len(msg.raw_mentions) + len(msg.raw_role_mentions) + len(everyoneRegex.findall(msg.content)) >= 3:
        mentions = automod.mentions
        if await checks.ignores_automod(ctx):
            return

        lenMentions = sum(m != ctx.author.id for m in msg.raw_mentions) + len(msg.raw_role_mentions)

        if not mentions.state:
            return

        if channel.id in mentions.whitelist:
            return

        if mentions.everyone:
            lenMentions += len(everyoneRegex.findall(msg.content))

        if lenMentions >= mentions.count:
            if mentions.state == 5:
                return await add_points(ctx, mentions.points, 'Mentions')
            else:
                return await managePunishment(ctx, mentions.state, 'Caps')
