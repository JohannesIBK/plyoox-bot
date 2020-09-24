import datetime
import json
import re
import time

import discord

from utils.ext import standards as std, checks, context, logs

# Regex to find special things in messages
DISCORD_INVITE = '(discord(app\.com\/invite|\.com(\/invite)?|\.gg)\/?[a-zA-Z0-9-]{2,32})'
EXTERNAL_LINK = '((https?:\/\/(www\.)?|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})'
EVERYONE_MENTION = '@(here|everyone)'
discordRegex = re.compile(DISCORD_INVITE, re.IGNORECASE)
linkRegex = re.compile(EXTERNAL_LINK, re.IGNORECASE)
everyoneRegex = re.compile(EVERYONE_MENTION)


# find a specific word
def findWord(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search


# manage punishments for users if they send a forbidden word or smth else
async def managePunishment(ctx, punishment, reason):
    # delete the message the user sent
    await ctx.message.delete()
    user: discord.Member = ctx.author
    # cut the message down if the message is to long due discord limitation
    msg = ctx.message.content if len(ctx.message.content) < 1015 else f'{ctx.message.content[:1015]}...'
    reason = f'Automoderation: {reason}'

    # get predesigned embeds to have an consistend style and set some fields
    embed: discord.Embed = std.getBaseModEmbed(reason, ctx.author, ctx.me)
    userEmbed: discord.Embed = std.getBaseModEmbed(reason)
    userEmbed.add_field(name=f'{std.folder_emoji} **Server**', value=ctx.guild.name, inline=False)
    userEmbed.add_field(name=f'{std.list_emoji} **__Message__**', value=msg, inline=False)
    embed.add_field(name=f'{std.channel_emoji} **__Channel__**', value=ctx.channel.mention, inline=False)
    embed.add_field(name=f'{std.list_emoji} **__Message__**', value=msg, inline=False)

    data = await ctx.bot.db.fetchrow('SELECT bantime, mutetime, muterole FROM automod.config WHERE sid = $1', ctx.guild.id)

    # check which punishment the user get (a server-admin must set this on the web dashboard
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
        # check if the bot has the permissions to ban members
        if checks.hasPermsByName(ctx, ctx.me, 'ban_members'):
            embed.title = 'AUTOMODERATION [TEMPBAN]'
            userEmbed.title = 'AUTOMODERATION [TEMPBAN]'
            unixTime = time.time() + data['bantime']
            embed.add_field(name=f'{std.date_emoji} **__Entbann__**', value=datetime.datetime.fromtimestamp(unixTime).strftime('%d. %m. %Y um %H:%M:%S'))
            # if it is a tempban save the date of unban
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, 0, unixTime, json.dumps({'reason': reason}))
            await ctx.guild.ban(user, reason=reason)
    elif punishment == 4:
        if checks.hasPermsByName(ctx, ctx.me, 'manage_roles'):
            muteRole = ctx.guild.get_role(data['muterole'])
            if muteRole is None:
                return

            embed.title = 'AUTOMODERATION [TEMPMUTE]'
            userEmbed.title = 'AUTOMODERATION [TEMPMUTE]'
            unixTime = time.time() + data['mutetime']
            embed.add_field(name=f'{std.date_emoji} **__Entmute__**', value=datetime.datetime.fromtimestamp(unixTime).strftime('%d. %m. %Y um %H:%M:%S'))
            await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                 ctx.guild.id, user.id, 1, unixTime, json.dumps({'reason': reason}))
            await user.add_roles(muteRole, reason=reason)

    # run a function that handles the sent of the message to user and log channel
    await logs.createEmbedLog(ctx=ctx, modEmbed=embed, userEmbed=userEmbed, member=user, ignoreMMSG=True, ignoreNoLogging=True)


# add the user points and punish him, if nessassery (user reaches max number of points
async def add_points(ctx: context, addPoints, modType, user: discord.Member = None):
    # delete the message of the user
    await ctx.message.delete()

    # if a user is given, take it, else take the message author
    if user is not None:
        punishedUser: discord.Member = user
    else:
        punishedUser: discord.Message = ctx.author

    # add points, time and reason to the database
    await ctx.bot.db.execute(
        'INSERT INTO automod.users (uid, sid, points, time, reason) VALUES ($1, $2, $3, $4, $5)',
        punishedUser.id, ctx.guild.id, addPoints, time.time(), f'Automoderation: {modType}')

    # get the points the user have AND the settings for the guild
    points  = await ctx.bot.db.fetchval('SELECT sum(points) FROM automod.users WHERE uid = $1 AND sid = $2 AND $3 - time < 2592000', punishedUser.id, ctx.guild.id, time.time())
    data = await ctx.bot.db.fetchrow("SELECT action, maxpoints, muterole, mutetime, bantime FROM automod.config WHERE sid = $1", ctx.guild.id)
    msg: discord.Message = ctx.message

    action = data['action']
    maxPoints = data['maxpoints']
    unixTimeMute = unixTimeBan = time.time() + 86400

    if data['mutetime']:
        unixTimeMute: float = time.time() + data['mutetime']
    if data['bantime']:
        unixTimeBan: float = time.time() + data['bantime']

    # cut message down, if to long
    message = msg.content if len(msg.content) < 1015 else f'{ctx.message.content[:1015]}...'

    # handle message sending
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

    # check if user reached the max ammount of points, if yes punish him
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
                muteRole = ctx.guild.get_role(data['muterole'])
                if muteRole is None:
                    return

                embed.add_field(name=f'{std.date_emoji} **__Entmute__**', value=datetime.datetime.fromtimestamp(unixTimeMute).strftime('%d. %m. %Y um %H:%M:%S'))
                embed.title = 'AUTOMODERATION [TEMPMUTE]'
                await punishedUser.add_roles(muteRole, reason='Automoderation')
                await ctx.bot.db.execute("DELETE FROM automod.users WHERE uid = $1 AND sid = $2", punishedUser.id, msg.guild.id)
                await ctx.db.execute('INSERT INTO extra.timers (sid, objid, type, time, data) VALUES ($1, $2, $3, $4, $5)',
                                     ctx.guild.id, punishedUser.id, 1, unixTimeMute, json.dumps({'reason': 'Automoderation: Punktesystem'}))
            else:
                return
    await logs.createEmbedLog(ctx=ctx, modEmbed=embed, userEmbed=userEmbed, member=punishedUser, ignoreNoLogging=True, ignoreMMSG=True)


# function that checks the message if any rules got broken
async def automod(ctx):
    bot = ctx.bot
    guild: discord.Guild = ctx.guild
    msg: discord.Message = ctx.message
    channel: discord.TextChannel = ctx.channel

    # check if the server has this module activated
    if not await bot.get(guild.id, 'automod'):
        return

    # get the state of the word blacklist
    blState = await bot.get(guild.id, 'state')

    if blState:
        # get the forbidden words
        words = await bot.get(guild.id, 'words')
        # check if list is not empty or None
        if words:
            for word in words:
                if findWord(word)(msg.content.lower()):
                    # word is in the message. Check if User is allowed to send it
                    if not await checks.ignores_automod(ctx):
                        data = await bot.db.fetchrow('SELECT points, whitelist FROM automod.blacklist WHERE sid = $1', guild.id)

                        # check if channel is in the whitelist
                        if data['whitelist'] is not None:
                            if channel.id in data['whitelist']:
                                return

                        # check how to punish the user
                        if blState == 5:
                            return await add_points(ctx, data['points'], 'Blacklisted Word')
                        else:
                            return await managePunishment(ctx, blState, 'Blacklisted Word')

    # check if the message contains a discord Invite
    if discordRegex.findall(msg.content):
        # check if the user is allowed to send it
        if await checks.ignores_automod(ctx):
            return

        data = await bot.db.fetchrow("SELECT state, whitelist, partner, points FROM automod.invites WHERE sid = $1", guild.id)
        if not data:
            return

        # check if the check is deactivated on this server
        if not (state := data['state']):
            return

        # check if the channel is whitelisted
        if data['whitelist'] is not None:
            if channel.id in data['whitelist']:
                return

        # get whitelisted servers
        whitelistedServers = [guild.id]
        if partner := data['partner']:
            whitelistedServers.extend([int(guildID) for guildID in partner])

        # get invite data from discord and check if the Invite is valid or from a guild that is whitelisted
        hasInvite: bool = False
        for invite in discordRegex.findall(msg.content):
            try:
                invite = await bot.fetch_invite(invite[0])
            except discord.NotFound:
                continue

            except discord.Forbidden:
                # user is banned from inviters server
                if state == 5:
                    return await add_points(ctx, data['points'], 'Invite')
                else:
                    return await managePunishment(ctx, state, 'Invite')

            if invite.guild.id not in whitelistedServers:
                hasInvite = True
                break

        # message has an invite - punish
        if hasInvite:
            if state == 5:
                return await add_points(ctx, data['points'], 'Invite')
            else:
                return await managePunishment(ctx, state, 'Invite')

    # check if the message contains a link
    elif linkRegex.findall(msg.content):
        if await checks.ignores_automod(ctx):
            return

        data = await bot.db.fetchrow('SELECT points, state, links, whitelist, iswhitelist FROM automod.links WHERE sid = $1', guild.id)
        if not data:
            return

        if not (state := data['state']):
            return

        if data['whitelist'] is not None:
            if channel.id in data['whitelist']:
                return

        # allowed links
        links = ['discord.gg', 'discord.com', 'discordapp.com', 'plyoox.net']
        if (linksData := data['links']) is not None:
            links.extend(linksData)

        linksObj = linkRegex.findall(msg.content)
        for linkObj in linksObj:
            # get links in message
            link = linkObj[0].replace(linkObj[1], '')

            # check if link is allowed or not (link whitelist | link blacklist)
            if data['iswhitelist']:
                if link not in links:
                    if state == 5:
                        return await add_points(ctx, data['points'], 'Link')
                    else:
                        return await managePunishment(ctx, state, 'Link')
            else:
                if link in links:
                    if state == 5:
                        return await add_points(ctx, data['points'], 'Link')
                    else:
                        return await managePunishment(ctx, state, 'Link')


    # check if the message has no caps or message smaller than characters
    if not msg.clean_content.islower() and len(msg.content) > 15:
        if await checks.ignores_automod(ctx):
            return

        # find all capitalized letters + ÄÖU
        lenCaps = len(re.findall(r'[A-ZÄÖÜ]', msg.clean_content))
        percent = lenCaps / len(msg.content)
        # check if over 70% are caps
        if percent > 0.7:
            data = await bot.db.fetchrow("SELECT points, state, whitelist FROM automod.caps WHERE sid = $1", msg.guild.id)
            if not data:
                return
            # check if it is activated
            if not (state := data['state']):
                return

            if data['whitelist'] is not None:
                if channel.id in data['whitelist']:
                    return

            if state == 5:
                return await add_points(ctx, data['points'], 'Caps')
            else:
                return await managePunishment(ctx, state, 'Caps')

    # check if mentions in a message are higher than 3
    if len(msg.raw_mentions) + len(msg.raw_role_mentions) + len(everyoneRegex.findall(msg.content)) >= 3:
        if await checks.ignores_automod(ctx):
            return

        # get all mentions
        lenMentions = sum(m != ctx.author.id for m in msg.raw_mentions) + len(msg.raw_role_mentions)
        data = await bot.db.fetchrow(
            "SELECT state, points, count, whitelist, everyone FROM automod.mentions WHERE sid = $1",
            guild.id)
        if not data:
            return

        if not (state := data['state']):
            return

        if data['whitelist'] is not None:
            if channel.id in data['whitelist']:
                return

        # check if everyone and here mentions should be countet as well
        if data['everyone']:
            lenMentions += len(everyoneRegex.findall(msg.content))

        # check if the mentions are more than allowed
        if lenMentions >= data['count']:
            if state == 5:
                return await add_points(ctx, data['points'], 'Mentions')
            else:
                return await managePunishment(ctx, state, 'Caps')
