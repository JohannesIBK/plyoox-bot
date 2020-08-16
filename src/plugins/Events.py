import re
import typing

import discord
from discord.ext import commands

import main
from other import db
from utils.ext import standards as std
from utils.ext.formatter import formatMessage

CHANNEL_REGEX = r'#\w+'

class Events(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    async def checkGuilds(self):
        await self.bot.wait_until_ready()
        guilds = self.bot.guilds
        dbGuilds = (entry['sid'] for entry in await self.bot.db.fetch('SELECT sid FROM config.guilds'))

        for guild in guilds:
            if guild.id not in dbGuilds:
                await db.gotAddet(self.bot, guild)
                bots = len(list(filter(lambda m: m.bot, guild.members)))
                embed = discord.Embed(color=discord.Color.green(), title="**__SERVER JOINED__**")
                embed.add_field(name="Name", value=guild.name, inline=False)
                embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}', inline=False)
                embed.add_field(name="Owner", value=guild.owner, inline=False)
                embed.add_field(name="Region", value=guild.region, inline=False)
                embed.add_field(name="Stats",
                                value=f'__Rollen:__ {len(guild.roles)}\n__TextChannel:__ {len(guild.text_channels)}\n'
                                      f'__VoiceChannels:__ {len(guild.voice_channels)}',
                                inline=False)
                await self.bot.get_channel(715260033926955070).send(embed=embed)


    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: typing.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]):
        guild: discord.Guild = channel.guild
        if not guild.me.guild_permissions.manage_channels:
            return

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

        query = 'SELECT welcomer.joinrole, config.modroles, config.muterole, leveling.noxprole, leveling.roles ' \
                'FROM automod.config LEFT JOIN config.leveling ON config.sid = leveling.sid ' \
                'LEFT JOIN config.welcomer ON config.sid =  welcomer.sid WHERE config.sid = $1'
        roles = await self.bot.db.fetchrow(query, role.guild.id)

        if roles is None:
            return

        if role.id == roles['joinrole']:
            return await self.bot.db.execute("UPDATE config.welcomer SET joinrole = NULL WHERE sid = $1", guild.id)

        if roles['noxprole'] == role.id:
            return await self.bot.db.execute("UPDATE config.leveling SET noxprole = NULL WHERE sid = $2", roles['noxprole'], guild.id)

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

        if channels is None:
            return

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
    async def on_guild_join(self, guild):
        await db.gotAddet(self.bot, guild)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(color=discord.Color.green(), title="**__SERVER JOINED__**")
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
        await self.bot.db.execute("DELETE FROM automod.users WHERE sid = $1", guild.id)
        await self.bot.db.execute("DELETE FROM extra.timers WHERE sid = $1", guild.id)
        await self.bot.db.execute("DELETE FROM extra.commands WHERE sid = $1", guild.id)

        await self.bot.redis.delete(guild.id)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(color=discord.Color.red(), title="**__SERVER LEAVED__**")
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

        data = await self.bot.db.fetchrow(
            'SELECT joinrole, joinmessage, joinrole, joinchannel, joindm, modules.welcomer, modules.globalbans FROM config.welcomer '
            'INNER JOIN config.modules ON welcomer.sid = modules.sid WHERE welcomer.sid = $1',
            guild.id)

        if not data or not data['welcomer']:
            return

        if data['globalbans']:
            banData = await self.bot.db.fetchrow('SELECT reason, userid FROM extra.globalbans WHERE userid = $1', member.id)
            if banData is not None and banData['reason'] and banData['userid']:
                reason = banData['reason']
                await guild.ban(member, reason=f"Globalban:\n{reason}")
                logchannel = await self.bot.db.fetchval('SELECT logchannel FROM automod.config WHERE config.sid = $1', guild.id)
                if logchannel:
                    embed: discord.Embed = std.getBaseModEmbed(f'Globalban: {reason}', member)
                    embed.title = f'Automoderation [GLOBALBAN]'
                    logchannel = member.guild.get_channel(logchannel)
                    if logchannel is not None:
                        await logchannel.send(embed=embed)
                return

        if data["joinmessage"] is not None and data["joinchannel"] is not None:
            channel: discord.TextChannel = guild.get_channel(data["joinchannel"])
            channels = re.findall(CHANNEL_REGEX, data["joinmessage"])
            msg = formatMessage(data["joinmessage"], member)

            for channelMention in channels:
                channelToMention = discord.utils.find(lambda c: c.name == channelMention[1:], guild.channels)
                if channelToMention is not None:
                    msg = msg.replace(channelMention, channelToMention.mention)

            if msg is None:
                return

            if data['joindm']:
                await member.send(msg)
            elif channel is not None:
                await channel.send(msg)

        if data["joinrole"] is not None:
            role: discord.Role = guild.get_role(data["joinrole"])
            try:
                await member.add_roles(role)
            except:
                pass

        punishData = await self.bot.db.fetchrow(
            'SELECT timers.type, config.muterole FROM automod.config INNER JOIN extra.timers '
            'ON config.sid=timers.sid WHERE config.sid = $1 AND timers.objid = $2 AND timers.type = 1',
            guild.id, member.id)

        if punishData is not None:
            muteroleID: int = punishData['muterole']
            muterole: discord.Role = guild.get_role(muteroleID)
            if muterole is not None:
                await member.add_roles(muterole)


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild: discord.Guild = member.guild
        data = await self.bot.db.fetchrow(
            'SELECT leavechannel, leavemessage, welcomer FROM config.welcomer INNER JOIN config.modules '
            'ON welcomer.sid = modules.sid WHERE welcomer.sid = $1',
            guild.id)

        if not data or not data['welcomer']:
            return

        if data["leavemessage"] is not None and data["leavechannel"] is not None:
            channel = member.guild.get_channel(int(data["leavechannel"]))
            msg = formatMessage(data['leavemessage'], member)
            if msg is not None and channel is not None:
                await channel.send(msg)


def setup(bot):
    bot.add_cog(Events(bot))
