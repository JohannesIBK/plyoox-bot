import asyncio
import json
import random
import re
import time
import dbl
import discord
import typing
from discord.ext import commands, tasks

import main
from others import db
from utils import automod
from utils.ext import standards as std, checks, context

DISCORD_INVITE = '(discord(app\.com\/invite|\.com(\/invite)?|\.gg)\/?[a-zA-Z0-9-]{2,32})'
EXTERNAL_LINK = '((https?:\/\/(www\.)?|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})'
BRACKET_REGEX = r'{.*?}'
discordRegex = re.compile(DISCORD_INVITE, re.IGNORECASE)
linkRegex = re.compile(EXTERNAL_LINK, re.IGNORECASE)


def findWord(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search


with open(r"./others/keys/dbl.env", 'r') as file:
    dblToken = file.read()


class Events(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.dblToken = dblToken
        self.dblpy = dbl.DBLClient(bot, self.dblToken)
        self.checkTimers.start()
        self.update_stats.start()

    @tasks.loop(minutes=15)
    async def checkTimers(self):
        entrys = await self.bot.db.fetch('SELECT * FROM extra.timers WHERE time - extract(EPOCH FROM now()) <= 900;')

        for entry in entrys:
            timerType = entry['type']
            endTime = entry['time']
            guildID = entry['sid']
            if timerType in [0, 1]:
                memberID = entry['objid']
                self.bot.loop.create_task(self.punishTimer(endTime, memberID, guildID, timerType))

            if timerType == 2:
                messageID = entry['objid']
                data = entry['data']
                self.bot.loop.create_task(self.giveawayTimer(endTime, messageID, data))

    @checkTimers.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

    async def punishTimer(self, unbanTime: int, memberID: int, guildID: int, punishmentType: str):
        """
        :param unbanTime: UNIX Timestamp when user's punishment runs out
        :param memberID: ID of Member
        :param guildID: ID of Guild
        :param punishmentType: Type of punishment
        :return
        """

        untilUnban = unbanTime - time.time()
        if unbanTime > 0:
            untilUnban = 0

        await asyncio.sleep(untilUnban)

        guild = self.bot.get_guild(guildID)
        self.bot.dispatch('punishment_runout', guild, memberID, punishmentType)

    async def giveawayTimer(self, endTime: int, messageID: int, data):

        untilEnd = endTime - time.time()
        if endTime > 0:
            untilEnd = 0

        await asyncio.sleep(untilEnd)

        data = json.loads(data)
        channel = self.bot.get_channel(data['channel'])
        message = await channel.fetch_message(messageID)
        self.bot.dispatch('giveaway_runout', message, data)

    async def automod(self, msg: discord.Message):
        ctx = await self.bot.get_context(msg, cls=context.Context)

        if not await self.bot.get(msg.guild.id, 'automod'):
            return

        if await self.bot.get(msg.guild.id, 'state'):
            words = await self.bot.get(msg.guild.id, 'words')
            if words:
                for word in words:
                    if findWord(word)(msg.content.lower()):
                        if not await checks.ignores_automod(ctx):
                            data = await self.bot.db.fetchrow(
                                'SELECT points, whitelist FROM automod.blacklist WHERE sid = $1', msg.guild.id)

                            if data['whitelist'] is not None and msg.channel.id in data['whitelist']:
                                return

                            return await automod.add_points(ctx, data['points'], 'Blacklisted Word')

        if discordRegex.findall(msg.content):
            if await checks.ignores_automod(ctx):
                return

            data = await self.bot.db.fetchrow(
                "SELECT state, whitelist, partner, points FROM automod.invites WHERE sid = $1",
                msg.guild.id)

            if not data['state']:
                return

            if data['whitelist'] is not None and msg.channel.id in data['whitelist']:
                return

            whitelistedServers = [msg.guild.id]
            if (partner := data['partner']):
                whitelistedServers.extend([int(guildID) for guildID in partner])

            hasInvite: bool = False

            for invite in discordRegex.findall(msg.content):
                try:
                    invite = await self.bot.fetch_invite(invite[0])
                except discord.NotFound:
                    continue

                except discord.Forbidden:
                    await automod.add_points(ctx, data['points'], 'Discord-Invite')
                    hasInvite = True
                    break

                if invite.guild.id not in whitelistedServers:
                    hasInvite = True
                    break

            if hasInvite:
                return await automod.add_points(ctx, data['points'], 'Discord-Invite')

        elif linkRegex.findall(msg.content):
            if await checks.ignores_automod(ctx):
                return

            data = await self.bot.db.fetchrow(
                'SELECT points, state, links, whitelist, iswhitelist FROM automod.links WHERE sid = $1',
                msg.guild.id)

            if not data['state']:
                return

            if data['whitelist'] is not None and msg.channel.id in data['whitelist']:
                return

            links = ['discord.gg', 'discord.com', 'discordapp.com', 'plyoox.net']
            if (linksData := data['links']) is not None:
                links.extend(linksData)

            linksObj = linkRegex.findall(msg.content)

            if data['iswhitelist']:
                for linkObj in linksObj:
                    link = linkObj[0].replace(linkObj[1], '')
                    if link not in links:
                        return await automod.add_points(ctx, data['points'], 'Link')
            else:
                for linkObj in linksObj:
                    link = linkObj[0].replace(linkObj[1], '')
                    if link in links:
                        return await automod.add_points(ctx, data['points'], 'Link')

        if not msg.clean_content.islower() and len(msg.content) > 15:
            if await checks.ignores_automod(ctx):
                return

            content = msg.clean_content.replace("Ü", "U").replace("Ä", "A").replace("Ö", "O")
            lenCaps = len(re.findall(r'[A-Z]', content))

            percent = lenCaps / len(msg.content)
            if percent > 0.7:
                data = await self.bot.db.fetchrow("SELECT points, state, whitelist FROM automod.caps WHERE sid = $1", msg.guild.id)

                if not data['state']:
                    return

                if data['whitelist'] and msg.channel.id in data['whitelist']:
                    return

                return await automod.add_points(ctx, data['points'], 'Caps')

        if len(msg.mentions) >= 3:
            if await checks.ignores_automod(ctx):
                return

            lenMentions = sum(not m.bot and m.id != msg.author.id for m in msg.mentions)
            data = await self.bot.db.fetchrow(
                "SELECT state, points, mentions_len, whitelist FROM automod.mentions WHERE sid = $1",
                msg.guild.id)

            if not data['state']:
                return

            if data['whitelist'] and msg.channel.id in data['whitelist']:
                return

            if lenMentions >= data['mentions_len']:
                return await automod.add_points(ctx, data['points'], 'Mentions')

    @tasks.loop(hours=6)
    async def update_stats(self):
        self.bot.logger.info('Attempting to post server count')
        try:
            await self.dblpy.post_guild_count()
            self.bot.logger.info('Posted server count ({})'.format(self.dblpy.guild_count()))
        except Exception as e:
            self.bot.logger.exception('Failed to post server count\n{}'.format(type(e).__name__))

    @update_stats.before_loop
    async def before_update_stats(self):
        if self.bot.user.id != 5054335413916622850:
            self.update_stats.cancel()
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_giveaway_runout(self, message: discord.Message, data):
        channel = message.channel
        reactions = message.reactions
        winners = []
        winnerCount = data['winner']
        win = data['winType']

        deleted: int = await self.bot.db.fetch('DELETE FROM extra.timers WHERE sid = $1 AND objid = $2', message.guild.id, message.id)
        print(deleted)

        if deleted == 0:
            return

        for reaction in reactions:
            if reaction.emoji == '🎉':
                users = await reaction.users().flatten()
                users.remove(message.guild.me)
                if len(users) <= winnerCount:
                    winners = users
                else:
                    for _ in range(winnerCount):
                        user = random.choice(users)
                        winners.append(user)
                        users.remove(user)
                break

        winnerMention = ' '.join(member.mention for member in winners)
        await channel.send(f'Gewinner von {data["winType"]} {"ist" if len(winners) == 1 else "sind"}\n{winnerMention}')
        await message.edit(embed=discord.Embed(color=std.normal_color,
                                               title=f"🎉 Giveaway",
                                               description=f'**Gewinn:** {win}\n'
                                                           f'**Gewinner:** {winnerMention}.\n'
                                                           f'ID: {message.id}'))

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: typing.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]):
        guild: discord.Guild = channel.guild
        muteRoleID = await self.bot.db.fetchval('SELECT muterole from automod.config WHERE sid = $1', guild.id)
        muteRole = guild.get_role(muteRoleID)
        if muteRole is None:
            return

        if isinstance(channel, discord.TextChannel):
            if channel.permissions_synced:
                return

            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2099776),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(muteRole, overwrite=overwrite)

        if isinstance(channel, discord.VoiceChannel):
            if channel.permissions_synced:
                return

            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2097664),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(muteRole, overwrite=overwrite)

        if isinstance(channel, discord.CategoryChannel):
            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2099776),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(muteRole, overwrite=overwrite)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild: discord.Guild = role.guild

        query = 'SELECT welcomer.joinrole, config.modroles, config.muterole, leveling.noxproles, leveling.roles ' \
                'FROM automod.config LEFT JOIN config.leveling ON config.sid = leveling.sid ' \
                'LEFT JOIN config.welcomer ON config.sid =  welcomer.sid WHERE config.sid = $1'
        roles = await self.bot.db.fetchrow(query, role.guild.id)

        if roles is None:
            return

        if role.id == roles['joinrole']:
            return await self.bot.db.execute("UPDATE config.welcomer SET joinrole = NULL WHERE sid = $1", guild.id)

        if (xpRoles := roles['noxproles']) is not None:
            if role.id in xpRoles:
                for xpRole in xpRoles:
                    if role.id == xpRole:
                        return await self.bot.db.execute("UPDATE config.leveling SET noxproles = array_remove(noxproles, $1) WHERE sid = $2", xpRole, guild.id)

        if (levelRoles := roles['roles']) is not None:
            if role.id in levelRoles:
                for lvlRole in levelRoles:
                    if lvlRole[0] == role.id:
                        return await self.bot.db.execute("UPDATE config.leveling SET roles = array_remove(roles, $1) WHERE sid = $2", lvlRole, guild.id)

        if (modRoles := roles['modroles']) is not None:
            if role.id in modRoles:
                for modRole in modRoles:
                    if role.id == modRole:
                        return await self.bot.db.execute("UPDATE automod.config SET modroles = array_remove(modroles, $1) WHERE sid = $2", role.id, guild.id)

        if role.id == roles['muterole']:
            return await self.bot.db.execute("UPDATE automod.config SET muterole = NULL WHERE sid = $1", guild.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild: discord.Guild = channel.guild

        query = 'SELECT welcomer.joinchannel, welcomer.leavechannel, leveling.channel AS lvlchannel, ' \
                'leveling.noxpchannels, config.logchannel FROM automod.config ' \
                'LEFT JOIN config.leveling ON config.sid = leveling.sid LEFT JOIN config.welcomer ' \
                'ON config.sid = welcomer.sid WHERE config.sid = $1'
        channels = await self.bot.db.fetchrow(query, guild.id)

        if channel.id == channels['joinchannel']:
            return await self.bot.db.execute("UPDATE config.welcomer SET joinchannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['leavechannel']:
            return await self.bot.db.execute("UPDATE config.welcomer SET leavechannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['logchannel']:
            return await self.bot.db.execute("UPDATE automod.config SET logchannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['lvlchannel']:
            return await self.bot.db.execute("UPDATE config.leveling SET channel = NULL WHERE sid = $1", guild.id)

        if (noXpChannels := channels['noxpchannels']) is not None:
            if channel.id in noXpChannels:
                for noXpChannel in noXpChannels:
                    if channel.id == noXpChannel:
                        return await self.bot.db.execute("UPDATE config.leveling SET noxpchannels = array_remove(noxpchannels, $1) WHERE sid = $2", noXpChannel, guild.id)

    @commands.Cog.listener()
    async def on_punishment_runout(self, guild: discord.Guild, memberID: int, punishType: int):
        if guild is None:
            return

        if punishType == 0:
            user = discord.Object(id=memberID)
            if user is None:
                return

            try:
                await guild.unban(user, reason='Tempban has expired')
            except discord.NotFound:
                pass
            await self.bot.db.execute(
                "DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = $3",
                guild.id, memberID, punishType)

        if punishType == 1:
            muteroleID: int = await self.bot.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', guild.id)
            muterole: discord.Role = guild.get_role(muteroleID)
            member: discord.Member = guild.get_member(memberID)

            if muterole is None or member is None:
                return

            try:
                await member.remove_roles(muterole)
                await self.bot.db.execute(
                    "DELETE FROM extra.timers WHERE sid = $1 AND objid = $2 and type = $3",
                    guild.id, memberID, punishType)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await db.gotAddet(self.bot, guild)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(
            color=std.normal_color,
            title="**__SERVER JOINED__**",
        )
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}', inline=False)
        embed.add_field(name="Owner", value=guild.owner, inline=False)
        embed.add_field(name="Region", value=guild.region, inline=False)
        embed.add_field(name="Stats",
                        value=f'__Rollen:__ {len(guild.roles)}\n__TextChannel:__ {len(guild.text_channels)}\n__VoiceChannels:__ {len(guild.voice_channels)}',
                        inline=False)
        await self.bot.get_channel(715260033926955070).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM config.guild WHERE sid = $1", guild.id)
        await self.bot.redis.delete(guild.id)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(
            color=std.normal_color,
            title="**__SERVER LEAVED__**",
        )
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}', inline=False)
        embed.add_field(name="Owner", value=guild.owner, inline=False)
        embed.add_field(name="Region", value=guild.region, inline=False)
        embed.add_field(name="Stats",
                        value=f'__Rollen:__ {len(guild.roles)}\n__TextChannel:__ {len(guild.text_channels)}\n__VoiceChannels:__ {len(guild.voice_channels)}',
                        inline=False)
        await self.bot.get_channel(715260033926955070).send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild: discord.Guild = member.guild

        query = 'SELECT joinrole, joinmessage, joinrole, joinchannel, joindm, modules.welcomer, modules.globalbans FROM config.welcomer ' \
                'INNER JOIN config.modules ON welcomer.sid = modules.sid WHERE welcomer.sid = $1'
        data = await self.bot.db.fetchrow(query, guild.id)

        if not data or not data['welcomer']:
            return

        if data['globalbans']:
            banData = await self.bot.db.fetchrow(
                'SELECT bans.reason, bans.userid, config.logchannel FROM extra.globalbans AS bans, '
                'automod.config AS config WHERE bans.userid = $1 OR config.sid = $2',
                member.id, guild.id)
            if (reason := banData['reason']) and banData['userid']:
                await guild.ban(member, reason=banData['reason'])
                if banData['logchannel']:
                    embed: discord.Embed = std.getBaseModEmbed(f'Globalban: {reason}]', member)
                    embed.title = f'Automoderation [GLOBALBAN]'
                    logchannel = member.guild.get_channel(banData['logchannel'])
                    if logchannel is not None:
                        await logchannel.send(embed=embed)
                return

        if (msg := data["joinmessage"]) is not None and data["joinchannel"] is not None:
            try:
                placeholders = re.findall(BRACKET_REGEX, msg)

                for placeholder in placeholders:
                    if placeholder.lower() == '{userm}':
                        msg = msg.replace(placeholder, member.mention)
                    elif placeholder.lower() == '{user}':
                        msg = msg.replace(placeholder, str(member))

                if data['joindm']:
                    await member.send(msg)
                else:
                    channel: discord.TextChannel = guild.get_channel(int(data["joinchannel"]))
                    await channel.send(msg)
            except discord.Forbidden:
                pass

        if (roleID := data["joinrole"]) is not None:
            role: discord.Role = guild.get_role(roleID)
            try:
                await member.add_roles(role)
            except:
                pass

        punishData = await self.bot.db.fetchrow(
            'SELECT timers.type, config.muterole FROM automod.config INNER JOIN extra.timers '
            'ON config.sid=timers.sid WHERE config.sid = $1 AND timers.objid = $2 AND timers.type = 1',
            guild.id, member.id)

        if punishData is None:
            return
        else:
            muteroleID: int = punishData['muterole']
            muterole: discord.Role = guild.get_role(muteroleID)
            if muterole is not None:
                await member.add_roles(muterole)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild: discord.Guild = member.guild

        query = 'SELECT leavechannel, leavemessage, welcomer FROM config.welcomer ' \
                'INNER JOIN config.modules ON welcomer.sid = modules.sid WHERE welcomer.sid = $1'
        data = await self.bot.db.fetchrow(query, guild.id)

        if not data or not data['welcomer']:
            return

        if (msg := data["leavemessage"]) is not None and data["leavechannel"] is not None:
            placeholders = re.findall(BRACKET_REGEX, msg)

            for placeholder in placeholders:
                if placeholder.lower() == '{user}':
                    msg = msg.replace(placeholder, str(member))

            try:
                channel: discord.TextChannel = member.guild.get_channel(int(data["leavechannel"]))
                await channel.send(msg)
            except:
                pass

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if not isinstance(msg.author, discord.Member):
            return

        await self.automod(msg)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
        await self.bot.db.execute("DELETE FROM automod.users WHERE key = $1", f'{user.id}{guild.id}')

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return

        if not isinstance(before.author, discord.Member):
            return

        if not before.created_at or not after.edited_at:
            return

        if before.content == after.content:
            return

        await self.automod(after)

        if (after.edited_at - before.created_at).seconds <= 30:
            await self.bot.process_commands(after)


def setup(bot):
    bot.add_cog(Events(bot))
