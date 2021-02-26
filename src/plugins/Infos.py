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
        roles.reverse()
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
    def _get_emojis(emojis):
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
    def _get_badges(flags: discord.PublicUserFlags):
        flag_list = []
        if flags.staff:
            flag_list.append(std.staff_emoji)
        if flags.partner:
            flag_list.append(std.partner_emoji)
        if flags.bug_hunter:
            flag_list.append(std.bughunter_badge)
        if flags.early_supporter:
            flag_list.append(std.supporter_emoji)
        if flags.hypesquad:
            flag_list.append(std.hypesquad_emoji)
        if flags.hypesquad_balance:
            flag_list.append(std.balance_emoji)
        if flags.hypesquad_brilliance:
            flag_list.append(std.brilliance_emoji)
        if flags.hypesquad_bravery:
            flag_list.append(std.bravery_emoji)
        if flags.verified_bot_developer:
            flag_list.append(std.botdev_emoji)
        if flags.bug_hunter_level_2:
            flag_list.append(std.bughunter2_badge)

        return flag_list

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
    async def server(self, ctx: context.Context, guildID=None):
        lang = await ctx.lang(utils=True)

        guild = ctx.guild
        if guildID is not None:
            if ctx.author.id == self.bot.owner_id:
                try:
                    foreign_guild = self.bot.get_guild(int(guildID))
                    if foreign_guild is not None:
                        guild = foreign_guild
                except TypeError:
                    pass

        boosts = {1: 2, 2: 15, 3: 30}
        roles = self._getRoles(guild.roles)
        emojis = self._get_emojis(guild.emojis)
        created = guild.created_at.strftime(lang["date.format.small"])
        days = datetime.datetime.utcnow() - guild.created_at

        embed = discord.Embed(color=std.normal_color, title=lang["info.embed.title"].format(
            n=guild.name))
        embed.set_thumbnail(url=guild.icon_url)
        embed.description = std.quote(lang["guild.embed.description"].format(g=guild))
        embed.add_field(
            name=std.arrow + lang["guild.embed.members.name"],
            value=f'```{guild.member_count}```',
            inline=False
        )
        embed.add_field(
            name=std.arrow + lang["guild.embed.data.name"],
            value=lang["guild.embed.data.value"].format(c=created, d=str(days)),
            inline=False
        )
        embed.add_field(
            name=std.arrow + lang["info.embed.roles.name"].format(r=str(len(guild.roles))),
            value=roles,
            inline=False
        )
        embed.add_field(
            name=std.arrow + lang["guild.embed.channels.name"],
            value=std.quote(lang["guild.embed.channels.value"].format(
                a=str(len(guild.channels)),
                t=str(len(guild.text_channels)),
                v=str(len(guild.voice_channels)),
                c=str(len(guild.categories)))),
            inline=False
        )
        embed.add_field(
            name=std.arrow + lang["guild.embed.boosts.name"].format(l=str(guild.premium_tier)),
            value=std.quote(lang["guild.embed.boosts.value"]
                            .format(b=str(guild.premium_subscription_count),
                                    m=str(boosts[min(guild.premium_tier + 1, 3)]))),
            inline=False
        )
        embed.add_field(
            name=std.arrow + lang["guild.embed.emojis.name"].format(e=str(len(guild.emojis))),
            value=emojis,
            inline=False
        )
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd(aliases=['user', 'whois'])
    async def info(self, ctx: context.Context, user: discord.Member = None):
        lang = await ctx.lang(utils=True)

        def sort(val):
            return val.joined_at

        if user is None:
            user = ctx.message.author
        joined_dc = user.created_at.strftime(lang["date.format.small"])
        days_dc = (datetime.datetime.now() - user.created_at).days
        joined_guild = user.joined_at.strftime(lang["date.format.small"])
        since_joined_guild = (datetime.datetime.now() - user.joined_at).days
        roles = self._getRoles(user.roles)
        members = ctx.guild.members
        flags = self._get_badges(user.public_flags)
        members.sort(key=sort)
        join_pos = members.index(user) + 1

        embed = discord.Embed(title=lang["info.embed.title"].format(n=user.display_name),
                              color=user.color)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = std.quote(lang["info.embed.description"].format(u=user))
        embed.add_field(name=std.arrow + lang["info.embed.account.name"],
                        value=std.quote(lang["info.embed.account.value"].format(
                            jd=joined_dc,
                            dd=str(days_dc))),
                        inline=False)
        embed.add_field(name=std.arrow + lang["info.embed.server.name"],
                        value=std.quote(lang["info.embed.server.value"].format(
                            jg=joined_guild,
                            sjg=str(since_joined_guild),
                            jp=str(join_pos))),
                        inline=False)
        embed.add_field(name=std.arrow + lang["info.embed.roles.name"].format(
            r=str(len(user.roles) - 1)),
                        value=str(roles),
                        inline=False)
        embed.add_field(name=std.arrow + lang["info.embed.falgs.name"].format(
            f=str(len(flags))),
                        value=' '.join(flags) if flags else '-----',
                        inline=False)

        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    async def todayJoined(self, ctx: context.Context):
        lang = await ctx.lang()

        joined = len([user.id for user in ctx.guild.members if
                      (datetime.datetime.now() - user.joined_at).seconds <= 86400])
        await ctx.embed(lang["todayjoined.message"].format(j=str(joined)), signed=True)

    @cmd()
    async def joined(self, ctx: context.Context, user: Union[discord.Member, int] = None):
        lang = await ctx.lang(utils=True)

        def sort(list_user):
            return list_user.joined_at

        if user is None:
            user = ctx.author

        members = [member for member in ctx.guild.members]
        members.sort(key=sort)

        if isinstance(user, discord.Member):
            join_pos = members.index(user)
            days = (datetime.datetime.now() - user.joined_at).days

        else:
            try:
                if user == 0:
                    raise IndexError
                join_pos = user - 1
                user = members[join_pos]
                days = (datetime.datetime.now() - user.joined_at).days
            except IndexError:
                return await ctx.error(lang["joined.error.invalidposition"])

        joined = user.joined_at.strftime(lang["date.format.small"])

        embed = discord.Embed(title=lang["joined.embed.title"], color=std.normal_color)
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.description = std.quote(lang["info.embed.server.value"].format(
            jg=joined,
            sjg=str(days),
            jp=str(join_pos + 1)))
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
        embed.add_field(name=std.arrow + lang["bot.embed.owner.name"],
                        value="```JohannesIBK#9220```")
        embed.add_field(name=std.arrow + lang["bot.embed.guilds.name"],
                        value=f'```{len(self.bot.guilds)}```')
        embed.add_field(name=std.arrow + lang["bot.embed.users.name"],
                        value=f'```{len(list(self.bot.get_all_members()))}```')
        embed.add_field(name=std.arrow + lang["bot.embed.versions.name"],
                        value=f'```Python: {python_version}\nDiscord.py: {discord.__version__}```')
        embed.add_field(name=f"{std.arrow}**Uptime**", value=f'```{uptime}```')
        embed.add_field(name="⠀",
                        value=f'[Vote](https://discordbots.org/bot/505433541916622850) | '
                              f'[{lang["bot.word.dashboard"]}](https://plyoox.net) | '
                              f'[{lang["bot.word.invite"]}](https://discordapp.com/oauth2/authorize'
                              f'?client_id={ctx.me.id}&scope=bot&permissions=285600894) | '
                              f'[{lang["bot.word.source"]}]('
                              f'https://github.com/JohannesIBK/plyoox-bot)',
                        inline=False)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    @checks.hasPerms(manage_guild=True)
    async def roleMembers(self, ctx: context.Context, role: discord.Role):
        lang = await ctx.lang()
        await ctx.embed(lang["role.message"].format(m=role.mention, l=len(role.members)),
                        signed=True)

    @cmd(aliases=["av"])
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
        await ctx.embed(lang["members.message"].format(m=str(ctx.guild.member_count)), signed=True)

    @cmd()
    async def dashboard(self, ctx: context.Context):
        await ctx.embed('https://plyoox.net/', signed=True)

    @cmd()
    async def vote(self, ctx: context.Context):
        lang = await ctx.lang()
        await ctx.embed(lang["vote.message"].format(l="https://top.gg/bot/505433541916622850/vote"),
                        signed=True)


def setup(bot):
    bot.add_cog(Infos(bot))
