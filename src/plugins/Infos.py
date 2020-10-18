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
    async def server(self, ctx: context.Context, guildID = None):
        lang = await ctx.lang(utils=True)

        guild = ctx.guild
        if guildID is not None:
            if ctx.author.id == self.bot.owner_id:
                try:
                    foreignGuild = self.bot.get_guild(int(guildID))
                    if foreignGuild is not None:
                        guild = foreignGuild
                except TypeError:
                    pass

        roles = self._getRoles(guild.roles)
        emojis = self._getEmojis(guild.emojis)
        created = guild.created_at.strftime(lang["smallDateFormat"])
        days = datetime.datetime.utcnow() - guild.created_at

        embed = discord.Embed(color=std.normal_color, title=lang["infoTitle"].format(n=guild.name))
        embed.set_thumbnail(url=guild.icon_url)
        embed.description = lang["guildDescription"].format(g=guild)
        embed.add_field(name=std.arrow + lang["guildMembersTitle"],
                        value=f'```{guild.member_count}```',
                        inline=False)
        embed.add_field(name=std.arrow + lang["guildDataTile"],
                        value=lang["guildDataField"].format(c=created, d=str(days)),
                        inline=False)
        embed.add_field(name=std.arrow + lang["infoRolesTitle"].format(r=str(len(guild.roles))),
                        value=roles,
                        inline=False)
        embed.add_field(name=std.arrow + lang["guildChannelTitle"],
                        value=lang["guildChannelField"].format(a=str(len(guild.channels)),
                                                               t=str(len(guild.text_channels)),
                                                               v=str(len(guild.voice_channels)),
                                                               c=str(len(guild.categories))))

        embed.add_field(name=std.arrow + lang["guildEmojisTitle"].format(e=str(len(guild.emojis))),
                        value=emojis,
                        inline=False)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd(aliases=['user', 'whois'])
    async def info(self, ctx: context.Context, user: discord.Member = None):
        lang = await ctx.lang(utils=True)

        def sort(val):
            return val.joined_at

        if user is None:
            user = ctx.message.author
        joined_dc = user.created_at.strftime(lang["smallDateFormat"])
        days_dc = (datetime.datetime.now() - user.created_at).days
        joined_guild = user.joined_at.strftime(lang["smallDateFormat"])
        since_joined_guild = (datetime.datetime.now() - user.joined_at).days
        roles = self._getRoles(user.roles)
        members = ctx.guild.members
        flags = self._getBadges(user.public_flags)
        members.sort(key=sort)
        join_pos = members.index(user) + 1

        embed = discord.Embed(title=lang["infoTitle"].format(n=user.display_name), color=user.color)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = lang["infoDescription"].format(u=user)
        embed.add_field(name=std.arrow + lang["infoAccountTitle"],
                        value=lang["infoAccountValue"].format(jd=joined_dc, dd=str(days_dc)),
                        inline=False)
        embed.add_field(name=std.arrow + lang["infoServerTitle"],
                        value=lang["infoServerValue"].format(jg=joined_guild, sjg=str(since_joined_guild), jp=str(join_pos)),
                        inline=False)
        embed.add_field(name=std.arrow + lang["infoRolesTitle"].format(r=str(len(user.roles) - 1)),
                        value=f'{roles}',
                        inline=False)
        embed.add_field(name=std.arrow + lang["infoFlagsTitle"].format(f=str(len(flags))), value=' '.join(flags) if flags else '-----')

        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    async def todayJoined(self, ctx: context.Context):
        lang = await ctx.lang()

        joined = len([user.id for user in ctx.guild.members if (datetime.datetime.now() - user.joined_at).seconds <= 86400])
        await ctx.embed(lang["todayMessage"].format(j=str(joined)), signed=True)

    @cmd()
    async def joined(self, ctx: context.Context, user: Union[discord.Member, int] = None):
        lang = await ctx.lang()

        def sort(list_user):
            return list_user.joined_at

        if user is None:
            user = ctx.author

        members = [member for member in ctx.guild.members]
        members.sort(key=sort)

        if isinstance(user, discord.Member):
            join_pos = members.index(user)
            user = user
            days = (datetime.datetime.now() - user.joined_at).days

        else:
            try:
                if user == 0:
                    raise IndexError
                join_pos = user - 1
                user = members[join_pos]
                days = (datetime.datetime.now() - user.joined_at).days
            except IndexError:
                return await ctx.error(lang["joinedError"])

        joined = user.joined_at.strftime(lang["smallDateFormat"])

        embed = discord.Embed(title=lang["joinedTitle"], color=std.normal_color)
        embed.add_field(name=std.arrow + lang["joinedFieldName"],
                        value=lang["joinedFieldValue"].format(p=str(join_pos + 1), d=str(days)))
        embed.add_field(name=std.arrow + lang["joinedFieldName"],
                        value=lang["infoServerValue"].format(jg=joined, sjg=str(days), jp=str(join_pos)))
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    async def bot(self, ctx: context.Context):
        lang = await ctx.lang(utils=True)
        uptime = datetime.timedelta(seconds=round(time.time() - self.bot.startTime))
        python_version = '{}.{}.{}'.format(*sys.version_info[:3])

        embed = std.getEmbed()
        embed.title = f'{ctx.me}'
        embed.add_field(name=std.arrow + lang["botOwner"], value="```JohannesIBK#9220```")
        embed.add_field(name=std.arrow + lang["botGuilds"], value=f'```{len(self.bot.guilds)}```')
        embed.add_field(name=std.arrow + lang["botUser"], value=f'```{len(list(self.bot.get_all_members()))}```')
        embed.add_field(name=std.arrow + lang["botVersions"],
                        value=f'```Python: {python_version}\nDiscord.py: {discord.__version__}```')
        embed.add_field(name=f"{std.arrow}**Uptime**", value=f'```{uptime}```')
        embed.add_field(name="⠀",
                        value=f'[Vote](https://discordbots.org/bot/505433541916622850) | '
                              f'[{lang["botDashboard"]}](https://plyoox.net) | '
                              f'[{lang["botInvite"]}](https://discordapp.com/oauth2/authorize?client_id={ctx.me.id}&scope=bot&permissions=285600894) | '
                              f'[{lang["botSource"]}](https://github.com/JohannesIBK/plyoox-bot)', inline=False)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    @checks.hasPerms(manage_guild=True)
    async def roleMembers(self, ctx: context.Context, role: discord.Role):
        lang = await ctx.lang()
        await ctx.embed(lang["roleMessage"].format(m=role.mention, l=len(role.members)), signed=True)

    @cmd()
    async def avatar(self, ctx: context.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author
        embed = discord.Embed(color=std.normal_color)
        embed.set_author(name=user, url=user.avatar_url, icon_url=user.avatar_url)
        embed.set_image(url=user.avatar_url)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    async def members(self, ctx: context.Context):
        lang = await ctx.lang()
        await ctx.embed(lang["membersMessage"].format(m=str(ctx.guild.member_count)), signed=True)

    @cmd()
    async def dashboard(self, ctx: context.Context):
        await ctx.embed('https://plyoox.net/', signed=True)

    @cmd()
    async def vote(self, ctx: context.Context):
        lang = await ctx.lang()
        await ctx.embed(lang["voteMessage"].format(l="https://top.gg/bot/505433541916622850/vote"), signed=True)


def setup(bot):
    bot.add_cog(Infos(bot))
