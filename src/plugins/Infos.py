import datetime
import sys
import time
from typing import Union

import discord
from discord.ext import commands

import main
from utils.ext import standards as std, checks, context
from utils.ext.cmds import cmd


class Infos(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @staticmethod
    def _getRoles(roles):
        roles = [f'{role.mention}' for role in roles if not role.is_default()]
        string = ''

        for role in roles:
            if len(string + str(role)) > 970:
                string += '...'
                break
            string += f'{role} '

        if string == '':
            return '-----'
        else:
            return string

    @staticmethod
    def _getEmojis(emojis):
        emojis = [f'{emoji}' for emoji in emojis]
        string = ''

        for emoji in emojis:
            if len(string + str(emoji)) > 1015:
                string += '...'
                break
            string += emoji

        if string == '':
            return '-----'
        else:
            return string

    @staticmethod
    def _getBadges(flags: discord.PublicUserFlags):
        flagList = []
        if flags.staff:
            flagList.append(std.staff_emoji)
        if flags.partner:
            flagList.append(std.partner_emoji)
        if flags.bug_hunter:
            flagList.append(std.bughunter_badge)
        if flags.early_supporter:
            flagList.append(std.supporter_emoji)
        if flags.hypesquad:
            flagList.append(std.hypesquad_emoji)
        if flags.hypesquad_balance:
            flagList.append(std.balance_emoji)
        if flags.hypesquad_brilliance:
            flagList.append(std.brilliance_emoji)
        if flags.hypesquad_bravery:
            flagList.append(std.bravery_emoji)
        if flags.verified_bot_developer:
            flagList.append(std.botdev_emoji)
        if flags.bug_hunter_level_2:
            flagList.append(std.bughunter2_badge)

        return flagList

    @staticmethod
    def statusEmoji(status):
        status = str(status).lower()
        if status == 'online':
            return std.online_emoji
        if status == 'offline':
            return std.offline_emoji
        if status == 'idle':
            return std.idle_emoji
        if status == 'dnd':
            return std.dnd_emoji

    @cmd(aliases=["serverinfo", "guild"])
    async def server(self, ctx: context.Context, guildID: int = None):
        guild: discord.Guild = ctx.guild
        if guildID is not None:
            if ctx.author.id == self.bot.owner_id:
                foreignGuild = self.bot.get_guild(guildID)
                if foreignGuild is not None:
                    guild = foreignGuild

        roles = self._getRoles(guild.roles)
        emojis = self._getEmojis(guild.emojis)

        idle_members = len(list(filter(lambda m: m.status == discord.Status.idle and not m.bot, guild.members)))
        online_members = len(list(filter(lambda m: m.status == discord.Status.online and not m.bot, guild.members)))
        offline_members = len(list(filter(lambda m: m.status == discord.Status.offline and not m.bot, guild.members)))
        dnd_members = len(list(filter(lambda m: m.status == discord.Status.dnd and not m.bot, guild.members)))
        bots = len([m.bot for m in guild.members if m.bot])

        embed = discord.Embed(color=std.normal_color, title=f'***__Info über {guild.name}__***')
        embed.set_thumbnail(url=guild.icon_url)
        embed.description = f'{std.nametag_emoji} **Name:** {guild.name}\n' \
                            f'{std.botdev_emoji} **ID**: {guild.id}\n' \
                            f'{std.owner_emoji} **Owner:** {guild.owner}\n' \
                            f'{std.globe_emoji} **Region:** {guild.region}\n' \
                            f'{std.lock_emoji} **Verification:** {guild.verification_level}\n'
        embed.add_field(name=f'{std.members_emoji} **Mitglieder** ({guild.member_count})',
                        value=f'{std.online_emoji}{online_members} '
                              f'{std.idle_emoji}{idle_members} '
                              f'{std.dnd_emoji}{dnd_members} '
                              f'{std.offline_emoji}{offline_members} '
                              f'{std.clyde_emoji}{bots}',
                        inline=False)
        embed.add_field(name=f'{std.date_emoji} **Daten**',
                        value=f'**Erstellt:** {guild.created_at.strftime("%d.%m.%Y")}\n'
                              f'**Tage seitdem:** {(datetime.datetime.now() - guild.created_at).days}',
                        inline=False)
        embed.add_field(name=f'{std.mention_emoji} **Rollen ({len(guild.roles) - 1})**',
                        value=roles,
                        inline=False)
        embed.add_field(name=f'{std.folder_emoji} **__Channel__**',
                        value=f'**Insgesamt:** {len(guild.channels)}\n'
                              f'**Text:** {len(guild.text_channels)}\n'
                              f'**Voice:** {len(guild.voice_channels)}\n'
                              f'**Kategorie:** {len(guild.categories)}')

        embed.add_field(name=f'{std.ola_emoji} **Emojis ({len(guild.emojis)})**',
                        value=emojis,
                        inline=False)

        await ctx.send(embed=embed)

    @cmd(aliases=['user', 'whois'])
    async def info(self, ctx: context.Context, user: commands.MemberConverter = None):
        def sort(val):
            return val.joined_at

        if user is None:
            user = ctx.message.author
        joined_dc = user.created_at.strftime("%d.%m.%Y")
        days_dc = (datetime.datetime.now() - user.created_at).days
        joined_guild = user.joined_at.strftime("%d.%m.%Y")
        since_joined_guild = (datetime.datetime.now() - user.joined_at).days
        roles = self._getRoles(user.roles)
        members = ctx.guild.members
        flags = self._getBadges(user.public_flags)
        members.sort(key=sort)
        join_pos = members.index(user) + 1

        embed = discord.Embed(title=f'__***Info über {user}***__', color=user.color)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = f'{std.botdev_emoji} **ID:** {user.id}\n' \
                            f'{std.nametag_emoji} **Name:** {user.display_name}\n' \
                            f'{std.mention_emoji} **Erwähnung:** {user.mention}'
        embed.add_field(name=f'{std.date_emoji} **Daten**',
                        value=f'**__Account__**\n'
                              f'Erstellt: {joined_dc}\n'
                              f'Tage seitdem: {days_dc}'
                              f'\n\n'
                              f'**__Server__**\n'
                              f'Beigetreten: {joined_guild}\n'
                              f'Tage seitdem: {since_joined_guild}\n'
                              f'Join-Position: {join_pos}',
                        inline=False)
        embed.add_field(name=f"{std.info_emoji} **Status**",
                        value=f'Desktop: {self.statusEmoji(user.desktop_status)}\n'
                              f'Handy: {self.statusEmoji(user.mobile_status)}\n'
                              f'Web: {self.statusEmoji(user.web_status)}\n',
                        inline=False)
        embed.add_field(name=f'{std.mention_emoji} **Rollen** ({len(user.roles) - 1})',
                        value=f'{roles}',
                        inline=False)
        embed.add_field(name=f'{std.folder_emoji} **Abzeichen** ({len(flags)})', value=' '.join(flags) if flags else '-----')

        if user.activity is not None:
            embed.add_field(name=f'{std.richPresence_emoji} **Aktivität**', value=user.activity.name, inline=False)

        await ctx.send(embed=embed)

    @cmd()
    async def todayJoined(self, ctx: context.Context):
        joined = len([user.id for user in ctx.guild.members if (datetime.datetime.now() - user.joined_at).days == 0])
        await ctx.embed(f'Heute {"ist" if joined == 1 else "sind"} {joined} User auf den Server gejoint.')

    @cmd()
    async def joined(self, ctx: context.Context, user: Union[commands.MemberConverter, int] = None):
        def sort(list_user):
            return list_user.joined_at

        if user is None:
            user = ctx.author

        all_members = [member for member in ctx.guild.members]
        all_members.sort(key=sort)

        if isinstance(user, discord.Member):
            join_pos = all_members.index(user)
            user = user
            days = (datetime.datetime.now() - user.joined_at).days

        else:
            try:
                if user == 0:
                    raise IndexError
                join_pos = user - 1
                user = all_members[join_pos]
                days = (datetime.datetime.now() - user.joined_at).days
            except IndexError:
                return await ctx.error('Kein User auf dieser Join Position.')

        embed = discord.Embed(title='Join Position:', color=std.normal_color)
        embed.add_field(name=f"{user}", value=f'Position: {join_pos + 1} (vor {days} Tagen)')
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cmd()
    async def bot(self, ctx: context.Context):
        uptime = datetime.timedelta(seconds=round(time.time() - self.bot.startTime))
        python_version = '{}.{}.{}'.format(*sys.version_info[:3])

        embed = std.getEmbed(f'{std.botdev_emoji} **ID:** {ctx.me.id}')
        embed.title = f'{ctx.me}'
        embed.add_field(name=f"{std.owner_emoji} **Owner**", value="JohannesIBK#9220", inline=False)
        embed.add_field(name=f"{std.folder_emoji} **Server**", value=str(len(self.bot.guilds)), inline=False)
        embed.add_field(name=f"{std.members_emoji} **User**", value=str(len(list(self.bot.get_all_members()))), inline=False)
        embed.add_field(name=f"{std.info_emoji} **Versions**",
                        value=f'**Python:** {python_version}\n**Discord.py:** {discord.__version__}', inline=False)
        embed.add_field(name=f"{std.date_emoji} **Uptime**", value=str(uptime), inline=False)
        embed.add_field(name="⠀",
                        value=f'[DBL](https://discordbots.org/bot/505433541916622850) | '
                              f'[Dashboard](https://plyoox.net) | '
                              f'[Invite](https://discordapp.com/oauth2/authorize?client_id={ctx.me.id}&scope=bot&permissions=285600894) | '
                              f'[Source-Code](https://github.com/JohannesIBK/plyoox-bot)')

        await ctx.send(embed=embed)

    @cmd()
    @checks.hasPerms(manage_guild=True)
    async def roleMembers(self, ctx: context.Context, role: discord.Role):
        await ctx.embed(f'Die Rolle {role.mention} hat {len(role.members)} Mitglieder.')

    @cmd()
    async def avatar(self, ctx: context.Context, user: commands.MemberConverter = None):
        if user is None:
            user = ctx.author
        embed: discord.Embed = discord.Embed(color=std.normal_color)
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        embed.set_image(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cmd()
    async def members(self, ctx: context.Context):
        await ctx.embed(f'Der Discord hat momentan `{ctx.guild.member_count}` Mitglieder.')

    @cmd()
    async def dashboard(self, ctx: context.Context):
        await ctx.send('https://plyoox.net/')

    @cmd()
    async def vote(self, ctx: context.Context):
        await ctx.embed('Vote [hier](https://top.gg/bot/505433541916622850/vote) für mich :D')


def setup(bot):
    bot.add_cog(Infos(bot))
