import logging
import typing

import discord
from discord.ext import commands

import main
from other import db
from utils.ext import standards as std
from utils.ext.formatter import formatMessage


class Events(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    async def checkGuilds(self):
        await self.bot.wait_until_ready()
        guilds = self.bot.guilds
        db_guilds = (entry['sid'] for entry in
                     await self.bot.db.fetch('SELECT sid FROM config.guild'))

        for guild in guilds:
            if guild.id not in db_guilds:
                await db.gotAddet(self.bot, guild)
                bots = len(list(filter(lambda m: m.bot, guild.members)))
                embed = discord.Embed(color=discord.Color.green(), title="**__SERVER JOINED__**")
                embed.add_field(name="Name", value=guild.name, inline=False)
                embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}',
                                inline=False)
                embed.add_field(name="Owner", value=guild.owner, inline=False)
                embed.add_field(name="Region", value=str(guild.region), inline=False)
                embed.add_field(name="Stats",
                                value=f'__Rollen:__ {len(guild.roles)}'
                                      f'\n__TextChannel:__ {len(guild.text_channels)}\n'
                                      f'__VoiceChannels:__ {len(guild.voice_channels)}',
                                inline=False)
                await self.bot.get_channel(715260033926955070).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: typing.Union[discord.TextChannel,
                                      discord.VoiceChannel, discord.CategoryChannel]):
        guild = channel.guild
        if not guild.me.guild_permissions.manage_channels:
            return

        mute_role_id = await self.bot.db.fetchval(
            'SELECT muterole from automod.config WHERE sid = $1', guild.id)
        mute_role = guild.get_role(mute_role_id)
        if mute_role is None:
            return

        if isinstance(channel, discord.TextChannel):
            if channel.permissions_synced:
                return

            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2099776),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(mute_role, overwrite=overwrite)

        if isinstance(channel, discord.VoiceChannel):
            if channel.permissions_synced:
                return

            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2097664),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(mute_role, overwrite=overwrite)

        if isinstance(channel, discord.CategoryChannel):
            overwrite = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(permissions=2099776),
                allow=discord.Permissions(permissions=0))
            return await channel.set_permissions(mute_role, overwrite=overwrite)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild

        roles = await self.bot.db.fetchrow(
            'SELECT welcomer.joinroles, config.modroles, config.muterole, leveling.noxprole, '
            'leveling.roles '
            'FROM automod.config LEFT JOIN config.leveling ON config.sid = leveling.sid '
            'LEFT JOIN config.welcomer ON config.sid =  welcomer.sid WHERE config.sid = $1',
            role.guild.id)

        if roles is None:
            return

        if roles['noxprole'] == role.id:
            return await self.bot.db.execute(
                "UPDATE config.leveling SET noxprole = NULL WHERE sid = $2", roles['noxprole'],
                guild.id)

        if (levelRoles := roles['roles']) is not None:
            if role.id in levelRoles:
                for lvlRole in levelRoles:
                    if lvlRole[0] == role.id:
                        return await self.bot.db.execute(
                            "UPDATE config.leveling SET roles = array_remove(roles, $1) "
                            "WHERE sid = $2",
                            lvlRole, guild.id)

        if (modRoles := roles['modroles']) is not None:
            if role.id in modRoles:
                for modRole in modRoles:
                    if role.id == modRole:
                        return await self.bot.db.execute(
                            "UPDATE automod.config SET modroles = array_remove(modroles, $1) "
                            "WHERE sid = $2",
                            role.id, guild.id)

        if (helperRoles := roles['helperroles']) is not None:
            if role.id in helperRoles:
                for helperRole in helperRoles:
                    if role.id == helperRole:
                        return await self.bot.db.execute(
                            "UPDATE automod.config SET helperroles = array_remove(helperroles, $1) "
                            "WHERE sid = $2",
                            role.id, guild.id)

        if (joinRoles := roles['joinroles']) is not None:
            if role.id in joinRoles:
                for joinRole in joinRoles:
                    if role.id == joinRole:
                        return await self.bot.db.execute(
                            "UPDATE config.welcomer SET joinroles = array_remove(joinroles, $1) "
                            "WHERE sid = $2",
                            role.id, guild.id)

        if role.id == roles['muterole']:
            return await self.bot.db.execute(
                "UPDATE automod.config SET muterole = NULL WHERE sid = $1", guild.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        channels = await self.bot.db.fetchrow(
            'SELECT welcomer.joinchannel, welcomer.leavechannel, leveling.channel AS lvlchannel, '
            'leveling.noxpchannels, config.logchannel FROM automod.config '
            'LEFT JOIN config.leveling ON config.sid = leveling.sid LEFT JOIN config.welcomer '
            'ON config.sid = welcomer.sid WHERE config.sid = $1',
            guild.id)

        if channels is None:
            return

        if channel.id == channels['joinchannel']:
            return await self.bot.db.execute(
                "UPDATE config.welcomer SET joinchannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['leavechannel']:
            return await self.bot.db.execute(
                "UPDATE config.welcomer SET leavechannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['logchannel']:
            return await self.bot.db.execute(
                "UPDATE automod.config SET logchannel = NULL WHERE sid = $1", guild.id)

        elif channel.id == channels['lvlchannel']:
            return await self.bot.db.execute(
                "UPDATE config.leveling SET channel = NULL WHERE sid = $1", guild.id)

        if (noXpChannels := channels['noxpchannels']) is not None:
            if channel.id in noXpChannels:
                for noXpChannel in noXpChannels:
                    if channel.id == noXpChannel:
                        return await self.bot.db.execute(
                            "UPDATE config.leveling SET noxpchannels = "
                            "array_remove(noxpchannels, $1) WHERE sid = $2",
                            noXpChannel, guild.id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await db.gotAddet(self.bot, guild)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(color=discord.Color.green(), title="**__SERVER JOINED__**")
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}',
                        inline=False)
        embed.add_field(name="Owner", value=guild.owner, inline=False)
        embed.add_field(name="Region", value=str(guild.region), inline=False)
        embed.add_field(name="Stats",
                        value=f'__Rollen:__ {len(guild.roles)}'
                              f'\n__TextChannel:__ {len(guild.text_channels)}'
                              f'\n__VoiceChannels:__ {len(guild.voice_channels)}',
                        inline=False)
        await self.bot.get_channel(715260033926955070).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM config.guild WHERE sid = $1", guild.id)
        await self.bot.db.execute("DELETE FROM automod.users WHERE sid = $1", guild.id)
        await self.bot.db.execute("DELETE FROM extra.timers WHERE sid = $1", guild.id)
        await self.bot.db.execute("DELETE FROM extra.commands WHERE sid = $1", guild.id)

        await self.bot.cache.remove(guild.id)

        bots = len(list(filter(lambda m: m.bot, guild.members)))
        embed = discord.Embed(color=discord.Color.red(), title="**__SERVER LEAVED__**")
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="Member", value=f'User: {len(guild.members)}\nBots: {bots}',
                        inline=False)
        embed.add_field(name="Owner", value=guild.owner, inline=False)
        embed.add_field(name="Region", value=guild.region, inline=False)
        embed.add_field(name="Stats",
                        value=f'__Rollen:__ {len(guild.roles)}'
                              f'\n__TextChannel:__ {len(guild.text_channels)}'
                              f'\n__VoiceChannels:__ {len(guild.voice_channels)}',
                        inline=False)
        await self.bot.get_channel(715260033926955070).send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        data = await self.bot.db.fetchrow(
            'SELECT joinmessage, joinroles, joinchannel, joinstate, modules.welcomer '
            'FROM config.welcomer '
            'FULL OUTER JOIN config.modules ON welcomer.sid = modules.sid WHERE welcomer.sid = $1',
            guild.id)

        if not data or not data['welcomer']:
            return

        if data["joinstate"] != "o" and data["joinmessage"]:
            msg = formatMessage(data["joinmessage"], member)

            if msg is None:
                return

            if data['joinstate'] == "d":
                await member.send(msg)
            elif data["joinstate"] == "c":
                channel = guild.get_channel(data["joinchannel"])
                await channel.send(msg)

        if data["joinroles"]:
            roles = []
            for _role in data["joinroles"]:
                _role = guild.get_role(_role)

                if _role is not None:
                    roles.append(_role)

            try:
                await member.add_roles(*roles)
            except discord.Forbidden:
                logging.info(f"Could not add role to {member.id}")

        punish_data = await self.bot.db.fetchrow(
            'SELECT timers.type, config.muterole FROM automod.config INNER JOIN extra.timers '
            'ON config.sid = timers.sid WHERE config.sid = $1 AND timers.objid = $2 AND '
            'timers.type = 1',
            guild.id, member.id)

        if punish_data:
            muterole_id: int = punish_data['muterole']
            muterole = guild.get_role(muterole_id)
            if muterole is not None:
                await member.add_roles(muterole)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        data = await self.bot.db.fetchrow(
            'SELECT leavechannel, leavemessage, leavestate, modules.welcomer FROM config.welcomer '
            'INNER JOIN config.modules ON welcomer.sid = modules.sid WHERE welcomer.sid = $1',
            member.guild.id)

        if not data or not data['welcomer'] or data["leavestate"] == "o":
            return

        if data["leavemessage"] and data["leavechannel"]:
            channel = member.guild.get_channel(data["leavechannel"])
            msg = formatMessage(data['leavemessage'], member)
            if msg is not None and channel is not None:
                await channel.send(msg)


def setup(bot):
    bot.add_cog(Events(bot))
