import datetime
import json
import re
import time

import discord

from utils.ext import standards as std, checks, logs
from utils.ext.context import Context

DISCORD_INVITE = '(discord(app\.com\/invite|\.com(\/invite)?|\.gg)\/?[a-zA-Z0-9-]{2,32})'
EXTERNAL_LINK = '((https?:\/\/(www\.)?|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})'
EVERYONE_MENTION = '@(here|everyone)'
discordRegex = re.compile(DISCORD_INVITE, re.IGNORECASE)
linkRegex = re.compile(EXTERNAL_LINK, re.IGNORECASE)
everyoneRegex = re.compile(EVERYONE_MENTION)


def findWord(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search


async def managePunishment(ctx: Context, punishment, reason):
    await ctx.message.delete()
    lang = await ctx.lang(module="automod", utils=True)
    config = await ctx.bot.cache.get(ctx.guild.id)
    if not config.automod:
        return
    config = config.automod.config

    user = ctx.author
    reason = lang["word.automod"] + ": " + reason

    punishment_str = ''
    date = None

    if punishment == 1:
        if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
            punishment_str = "kick"
            await ctx.guild.kick(user, reason=reason)
    elif punishment == 2:
        if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
            punishment_str = "ban"
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 3:
        if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
            punishment_str = "tempban"
            unixTime = time.time() + config.bantime
            date = datetime.datetime.utcfromtimestamp(unixTime)
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, "tempban", unixTime, json.dumps({'reason': reason}))
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 4:
        if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
            if config.muterole is None:
                return

            punishment_str = "tempmute"
            unixTime = time.time() + config.mutetime
            date = datetime.datetime.utcfromtimestamp(unixTime)
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, "tempmute", unixTime, json.dumps({'reason': reason}))
            await user.add_roles(config.muterole, reason=reason)

    mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason)
    user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType=punishment_str, duration=date)
    await logs.createLog(ctx, mEmbed=mod_embed, uEmbed=user_embed, automod=True)


async def add_points(ctx: Context, addPoints, reason, user: discord.Member = None):
    lang = await ctx.lang(module="automod", utils=True)
    await ctx.message.delete()
    config = await ctx.bot.cache.get(ctx.guild.id)
    if not config.automod:
        return
    config = config.automod.config

    if user is not None:
        punishedUser = user
    else:
        punishedUser = ctx.author

    await ctx.bot.db.execute(
        'INSERT INTO automod.users (uid, sid, points, time, reason) VALUES ($1, $2, $3, $4, $5)',
        punishedUser.id, ctx.guild.id, addPoints, time.time(), reason)

    points = await ctx.bot.db.fetchval(
        'SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2 AND $3 - time < 2592000',
        punishedUser.id, ctx.guild.id, time.time())

    action = config.action
    maxPoints = config.maxpoints
    unixTimeMute = unixTimeBan = time.time() + 86400

    if config.mutetime:
        unixTimeMute = time.time() + config.mutetime
    if config.bantime:
        unixTimeBan = time.time() + config.bantime

    date = None
    punishment_str = 'log'

    if points >= maxPoints and action is not None:
        if action == 1:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                punishment_str = 'kick'
                await ctx.guild.kick(punishedUser, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, ctx.guild.id)
            else:
                return

        if action == 2:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                punishment_str = "ban"
                await ctx.guild.ban(punishedUser, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, ctx.guild.id)
            else:
                return

        if action == 3:
            if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
                date = datetime.datetime.utcfromtimestamp(unixTimeBan)
                punishment_str = "tempban"
                await ctx.guild.ban(punishedUser, reason=lang["word.automod"] + ": " + reason)
                await ctx.db.execute(
                    'INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                    ctx.guild.id, punishedUser.id, 0, unixTimeBan, json.dumps({'reason': lang["word.automod"] + ": " + lang["word.tempban"]}))
            else:
                return
        if action == 4:
            if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
                if config.muterole is None:
                    return

                date = datetime.datetime.fromtimestamp(unixTimeMute)
                punishment_str = "tempmute"
                await punishedUser.add_roles(config.muterole, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, ctx.guild.id)
                await ctx.db.execute(
                    'INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                    ctx.guild.id, punishedUser.id, 1, unixTimeMute, json.dumps({'reason': lang["word.automod"] + ": " + reason}))
            else:
                return

    if user is not None:
        mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason, f"{points}/{maxPoints}", punishedUser)
    else:
        mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason, f"{points}/{maxPoints}")

    user_embed = std.automodUserEmbed(lang, reason, ctx.guild.name, punishment_str, f"{points}/{maxPoints}", date)

    await logs.createLog(ctx=ctx, mEmbed=mod_embed, uEmbed=user_embed, user=punishedUser, automod=True)


async def automod(ctx):
    bot = ctx.bot
    guild = ctx.guild
    msg = ctx.message
    channel = ctx.channel
    config = await bot.cache.get(ctx.guild.id)
    modules =  config.modules
    automod = config.automod
    lang = await ctx.lang(module="automod", utils=True)

    if not modules.automod or not config.automod:
        return

    if automod.blacklist.state:
        blacklist = automod.blacklist
        for word in blacklist.words:
            if findWord(word)(msg.content.lower()):
                if not await checks.ignoresAutomod(ctx):
                    if channel.id in blacklist.whitelist:
                        return

                    if blacklist.state == 5:
                        return await add_points(ctx, blacklist.points, lang["reason.blacklistedword"])
                    else:
                        return await managePunishment(ctx, blacklist.state, lang["reason.blacklistedword"])

    if discordRegex.findall(msg.content):
        invites = automod.invites
        if await checks.ignoresAutomod(ctx):
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
                    return await add_points(ctx, invites.points, lang["reason.invite"])
                else:
                    return await managePunishment(ctx, invites.state, lang["reason.invite"])

            if invite.guild.id not in whitelistedServers:
                hasInvite = True
                break

        if hasInvite:
            if invites.state == 5:
                return await add_points(ctx, invites.points, lang["reason.invite"])
            else:
                return await managePunishment(ctx, invites.state, lang["reason.invite"])


    elif linkRegex.findall(msg.content):
        links = automod.links
        if await checks.ignoresAutomod(ctx):
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
                        return await add_points(ctx, links.points, lang["reason.link"])
                    else:
                        return await managePunishment(ctx, links.state, lang["reason.link"])
            else:
                if link in links:
                    if links.state == 5:
                        return await add_points(ctx, links.points, lang["reason.link"])
                    else:
                        return await managePunishment(ctx, links.state, lang["reason.link"])


    if not msg.clean_content.islower() and len(msg.content) > 15:
        caps = automod.caps
        if await checks.ignoresAutomod(ctx):
            return

        lenCaps = len(re.findall(r'[A-ZÄÖÜ]', msg.clean_content))
        percent = lenCaps / len(msg.content)
        if percent > 0.7:
            if not caps.state:
                return

            if channel.id in caps.whitelist:
                return

            if caps.state == 5:
                return await add_points(ctx, caps.points, lang["reason.caps"])
            else:
                return await managePunishment(ctx, caps.state, lang["reason.caps"])

    if len(msg.raw_mentions) + len(msg.raw_role_mentions) + len(everyoneRegex.findall(msg.content)) >= 3:
        mentions = automod.mentions
        if await checks.ignoresAutomod(ctx):
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
                return await add_points(ctx, mentions.points, lang["reason.mentions"])
            else:
                return await managePunishment(ctx, mentions.state, lang["reason.mentions"])
