import datetime
import json
import re
import time

import discord

from utils.ext import standards as std, checks, logs
from utils.ext.context import Context

DISCORD_INVITE = r'(discord(app\.com\/invite|\.com(\/invite)?|\.gg)\/?[a-zA-Z0-9-]{2,32})'
EXTERNAL_LINK = r'((https?:\/\/(www\.)?|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})'
EVERYONE_MENTION = r'@(here|everyone)'
discordRegex = re.compile(DISCORD_INVITE, re.IGNORECASE)
linkRegex = re.compile(EXTERNAL_LINK, re.IGNORECASE)
everyoneRegex = re.compile(EVERYONE_MENTION)


def find_word(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search


async def manage_punishment(ctx: Context, punishment, reason):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        return

    lang = await ctx.lang(module=["automod", "moderation"], utils=True)
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
            unix_time = time.time() + config.bantime
            date = datetime.datetime.utcfromtimestamp(unix_time)
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, "tempban", unix_time, json.dumps({'reason': reason}))
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 4:
        if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
            if config.muterole is None:
                return

            punishment_str = "tempmute"
            unix_time = time.time() + config.mutetime
            date = datetime.datetime.utcfromtimestamp(unix_time)
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, "tempmute", unix_time, json.dumps({'reason': reason}))
            await user.add_roles(config.muterole, reason=reason)

    mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason)
    user_embed = std.dmEmbed(lang, reason=reason, guildName=ctx.guild.name, punishType=punishment_str, duration=date)
    await logs.createLog(ctx, mEmbed=mod_embed, uEmbed=user_embed, automod=True, user=user)


async def add_points(ctx: Context, new_points, reason, user: discord.Member = None):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

    lang = await ctx.lang(module="automod", utils=True)
    config = await ctx.bot.cache.get(ctx.guild.id)
    if not config.automod:
        return
    config = config.automod.config

    if user is not None:
        punished_user = user
    else:
        punished_user = ctx.author

    await ctx.bot.db.execute(
        'INSERT INTO automod.users (uid, sid, points, time, reason) VALUES ($1, $2, $3, $4, $5)',
        punished_user.id, ctx.guild.id, new_points, time.time(), reason)

    points = await ctx.bot.db.fetchval(
        'SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2 AND $3 - time < 2592000',
        punished_user.id, ctx.guild.id, time.time())

    action = config.action
    max_points = config.maxpoints
    unix_time_mute = unix_time_ban = time.time() + 86400

    if config.mutetime:
        unix_time_mute = time.time() + config.mutetime
    if config.bantime:
        unix_time_ban = time.time() + config.bantime

    date = None
    punishment_str = 'log'

    if points >= max_points and action is not None:
        if action == 1:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                punishment_str = 'kick'
                await ctx.guild.kick(punished_user, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punished_user.id, ctx.guild.id)
            else:
                return

        if action == 2:
            if checks.hasPermsByName(ctx, ctx.me, 'kick_members'):
                punishment_str = "ban"
                await ctx.guild.ban(punished_user, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punished_user.id, ctx.guild.id)
            else:
                return

        if action == 3:
            if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
                date = datetime.datetime.utcfromtimestamp(unix_time_ban)
                punishment_str = "tempban"
                await ctx.guild.ban(punished_user, reason=lang["word.automod"] + ": " + reason)
                await ctx.db.execute(
                    'INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                    ctx.guild.id, punished_user.id, 0, unix_time_ban, json.dumps({'reason': lang["word.automod"] + ": " + lang["word.tempban"]}))
            else:
                return
        if action == 4:
            if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
                if config.muterole is None:
                    return

                date = datetime.datetime.fromtimestamp(unix_time_mute)
                punishment_str = "tempmute"
                await punished_user.add_roles(config.muterole, reason=lang["word.automod"] + ": " + reason)
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punished_user.id, ctx.guild.id)
                await ctx.db.execute(
                    'INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                    ctx.guild.id, punished_user.id, 1, unix_time_mute, json.dumps({'reason': lang["word.automod"] + ": " + reason}))
            else:
                return

    if user is not None:
        mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason, f"{points}/{max_points}", punished_user)
    else:
        mod_embed = std.automodLog(ctx, punishment_str, lang, date, reason, f"{points}/{max_points}")

    user_embed = std.automodUserEmbed(lang, reason, ctx.guild.name, punishment_str, f"{points}/{max_points}", date)

    await logs.createLog(ctx=ctx, mEmbed=mod_embed, uEmbed=user_embed, user=punished_user, automod=True)


async def automod(ctx: Context):
    bot = ctx.bot
    guild = ctx.guild
    msg = ctx.message
    channel = ctx.channel
    config = await ctx.cache.get(ctx.guild.id)
    modules = config.modules
    automod_cf = config.automod
    lang = await ctx.lang(module=["automod", "moderation"], utils=True)

    if not modules.automod or not config.automod:
        return

    if automod_cf.blacklist.state:
        blacklist = automod_cf.blacklist
        for word in blacklist.words:
            if find_word(word)(msg.content.lower()):
                if not await checks.ignoresAutomod(ctx):
                    if channel.id in blacklist.whitelist:
                        return

                    if blacklist.state == 5:
                        return await add_points(ctx, blacklist.points, lang["reason.blacklistedword"])
                    else:
                        return await manage_punishment(ctx, blacklist.state, lang["reason.blacklistedword"])

    if discordRegex.findall(msg.content):
        invites = automod_cf.invites
        if await checks.ignoresAutomod(ctx):
            return

        if not invites.state:
            return

        if channel.id in invites.whitelist:
            return

        whitelisted_servers = [guild.id]
        whitelisted_servers.extend([int(guildID) for guildID in invites.partner])

        has_invite = False
        for invite in discordRegex.findall(msg.content):
            try:
                invite = await bot.fetch_invite(invite[0])
            except discord.NotFound:
                continue

            except discord.Forbidden:
                if invites.state == 5:
                    return await add_points(ctx, invites.points, lang["reason.invite"])
                else:
                    return await manage_punishment(ctx, invites.state, lang["reason.invite"])

            if invite.guild.id not in whitelisted_servers:
                has_invite = True
                break

        if has_invite:
            if invites.state == 5:
                return await add_points(ctx, invites.points, lang["reason.invite"])
            else:
                return await manage_punishment(ctx, invites.state, lang["reason.invite"])

    elif linkRegex.findall(msg.content):
        links = automod_cf.links
        if await checks.ignoresAutomod(ctx):
            return

        if not links.state:
            return

        if channel.id in links.whitelist:
            return

        links_list = ['discord.gg', 'discord.com', 'discordapp.com', 'plyoox.net']
        links_list.extend(links.links)

        links_obj = linkRegex.findall(msg.content)
        for linkObj in links_obj:
            link = linkObj[0].replace(linkObj[1], '')
            if links.iswhitelist:
                if link not in links_list:
                    if links.state == 5:
                        return await add_points(ctx, links.points, lang["reason.link"])
                    else:
                        return await manage_punishment(ctx, links.state, lang["reason.link"])
            else:
                if link in links:
                    if links.state == 5:
                        return await add_points(ctx, links.points, lang["reason.link"])
                    else:
                        return await manage_punishment(ctx, links.state, lang["reason.link"])

    if not msg.clean_content.islower() and len(msg.content) > 15:
        caps = automod_cf.caps
        if await checks.ignoresAutomod(ctx):
            return

        len_caps = len(re.findall(r'[A-ZÄÖÜ]', msg.clean_content))
        percent = len_caps / len(msg.content)
        if percent > 0.7:
            if not caps.state:
                return

            if channel.id in caps.whitelist:
                return

            if caps.state == 5:
                return await add_points(ctx, caps.points, lang["reason.caps"])
            else:
                return await manage_punishment(ctx, caps.state, lang["reason.caps"])

    if len(msg.raw_mentions) + len(msg.raw_role_mentions) + len(everyoneRegex.findall(msg.content)) >= 3:
        mentions = automod_cf.mentions
        if await checks.ignoresAutomod(ctx):
            return

        len_mentions = sum(m != ctx.author.id for m in msg.raw_mentions) + len(msg.raw_role_mentions)

        if not mentions.state:
            return

        if channel.id in mentions.whitelist:
            return

        if mentions.everyone:
            len_mentions += len(everyoneRegex.findall(msg.content))

        if len_mentions >= mentions.count:
            if mentions.state == 5:
                return await add_points(ctx, mentions.points, lang["reason.mentions"])
            else:
                return await manage_punishment(ctx, mentions.state, lang["reason.mentions"])
