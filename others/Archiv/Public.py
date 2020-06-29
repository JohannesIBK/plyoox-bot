import datetime
import random
import sys
import time

import discord
from discord.ext import commands

from utils.ext import standards


class Public(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------------statsics--------------------------------

    @staticmethod
    def _getRoles(roles):
        string = ""
        allRoles = []
        for role in roles:
            if not role.is_default():
                allRoles.insert(0, "%s " % role.mention)
        for aRole in allRoles:
            string += aRole

        if string is "":
            return "None"
        else:
            return string

    @staticmethod
    def _getEmojis(emojis):
        string = ''
        for emoji in emojis:
            string += f'{emoji}'
        if string is '':
            return 'None'
        else:
            return string[:1000]

    # --------------------------------commands--------------------------------

    @commands.command()
    async def info(self, ctx, User: discord.Member = None):
        lang = await self.bot.lang(ctx)

        if User is None:
            User = ctx.message.author

        roles = self._getRoles(User.roles)

        all_members = [member.joined_at for member in ctx.guild.members]
        all_members.sort()
        join_pos = all_members.index(User.joined_at) + 1

        embed = discord.Embed(title=lang['info'].format(user=User),
                              description=f'```ID: {User.id}```', color=User.color)
        embed.set_thumbnail(url=User.avatar_url)
        embed.add_field(name=lang['roles'], value=roles)
        embed.add_field(name=lang['joined_dc'],
                        value=lang['days_since_dc'].format(date=User.created_at.strftime("%d.%m.%Y um %H:%M:%S"), days=(datetime.datetime.now() - User.created_at).days, inline=False))
        embed.add_field(name=lang['joined_guild'],
                        value=lang['days_since_guild'].format(date=User.joined_at.strftime("%d.%m.%Y um %H:%M:%S"), since_days=(datetime.datetime.now() - User.joined_at).days, days=(User.joined_at - ctx.guild.created_at).days, join_pos=join_pos), inline=False)
        try:
            embed.add_field(name=lang['activity'], value=User.activity.name, inline=False)
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx):
        lang = await self.bot.lang(ctx)

        uptime = datetime.timedelta(seconds=round(time.time() - self.bot.startTime))

        await ctx.send(lang['message'].format(time=uptime))

    @commands.command(aliases=["serverinfo", "guild"])
    async def server(self, ctx):
        lang = await self.bot.lang(ctx)

        roles = self._getRoles(ctx.guild.roles)
        emojis = self._getEmojis(ctx.guild.emojis)

        idle_members = len(list(filter(lambda m: m.status == discord.Status.idle, ctx.guild.members)))
        online_members = len(list(filter(lambda m: m.status == discord.Status.online, ctx.guild.members)))
        offline_members = len(list(filter(lambda m: m.status == discord.Status.offline, ctx.guild.members)))
        dnd_members = len(list(filter(lambda m: m.status == discord.Status.dnd, ctx.guild.members)))

        embed = discord.Embed(color=standards.normal_color, title=ctx.guild.name,
                              description=f'```ID: {ctx.guild.id}```')
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=lang['owner'], value=ctx.guild.owner, inline=True)
        embed.add_field(name=lang['region'], value=ctx.guild.region, inline=True)
        embed.add_field(name=lang['members'], value=lang['members_msg'].format(member_count=ctx.guild.member_count, data=f'{standards.online_emoji}{online_members} {standards.idle_emoji}{idle_members} {standards.dnd_emoji}{dnd_members} {standards.offline_emoji}{offline_members}'), inline=True)
        embed.add_field(name=lang['created'], value=lang['created_text'].format(date=ctx.guild.created_at.strftime("%d.%m.%Y"), days=(datetime.datetime.now() - ctx.guild.created_at).days), inline=True)
        embed.add_field(name=lang['roles'], value=roles, inline=False)
        embed.add_field(name=lang['emojis'], value=emojis, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        embed = discord.Embed(title="[PRESS HERE]",
                              url=f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8",
                              color=standards.normal_color)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        ping = self.bot.latency * 1000
        start = time.perf_counter()
        message = await ctx.send(embed=discord.Embed(
            description=f'Pong!', color=standards.normal_color))
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(embed=discord.Embed(description='Bot: {:.2f}ms\nWebsocket: {:.2f}ms'.format(duration, ping), color=standards.normal_color))

    @commands.command(aliases=["source"])
    async def bot(self, ctx):
        uptime = datetime.timedelta(seconds=round(time.time() - self.bot.startTime))

        python_version = '{}.{}.{}'.format(*sys.version_info[:3])

        embed = discord.Embed(color=standards.normal_color)
        embed.add_field(name="**Owner**", value="JohannesIBK#9220", inline=False)
        embed.add_field(name="**Servers | Users**", value=f'{len(self.bot.guilds)} **|** {len(list(self.bot.get_all_members()))}', inline=True)
        embed.add_field(name="**Versions**", value=f'**Python:** {python_version}\n**Discord.py:** {discord.__version__}', inline=True)
        embed.add_field(name="**Uptime**", value=str(uptime))
        embed.add_field(name="⠀", value=f'[Github](https://github.com/JohannesIBK/HacklBot) | [DBL (upvote)](https://discordbots.org/bot/505433541916622850)')

        await ctx.send(embed=embed)

    @commands.command()
    async def someone(self, ctx):
        lang = await self.bot.lang(ctx)

        user = random.choice(ctx.guild.members)
        embed = discord.Embed(title=lang['random_user'], color=standards.normal_color)
        embed.add_field(name=f"{user} ( {user.mention} )", value=lang['joined'].format(days=(datetime.datetime.now() - user.joined_at).days))
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def joined(self, ctx, User: discord.Member = None):
        lang = await self.bot.lang(ctx)

        if User is None:
            User = ctx.author
        all_members = [member.joined_at for member in ctx.guild.members]
        all_members.sort()
        join_pos = all_members.index(User.joined_at) + 1
        embed = discord.Embed(title=lang['join_pos'], color=standards.normal_color)
        embed.add_field(name=f"{User}", value=lang['msg'].format(join_pos=join_pos, days=(datetime.datetime.now() - User.joined_at).days))
        embed.set_thumbnail(url=User.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def changelog(self, ctx):
        embed = discord.Embed(color=standards.normal_color, title="**Changelog**")

        v1_7 = "**[NEW]** Partner Sever -> Invites will not deleted" \
               "**[NEW]** Whitelist-Channels -> Automod ignores these channels." \
               "**[NEW]** noInvites instead off BanInvites & DeleteInvites"

        v1_6 = "**[NEW]** Bei Botting gebannte User werden nun in einer File mit Name und ID angegeben.\n" \
               "**[NEW]** Bei neuem Ticket werden nun die Mod-Rollen erwähnt werden.\n" \
               "**[NEW]** Channel-Support Benachrichtungen (PingChannel, SupportChannel).\n" \
               "**[FIXES]** Manche User werden nicht als User erkannt und verursachten einen Error."

        embed.add_field(name="Changelog 10.9", value=v1_6)
        embed.add_field(name="Changelog 18.9", value=v1_7)

        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('games')
    async def namehistory(self, ctx, Name: str):
        session = self.bot.session

        url_history_str = "https://api.mojang.com/user/profiles/{}/names"
        url = "https://api.mojang.com/profiles/minecraft"
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        payload = json.dumps(Name)

        response = await session.post(url, data=payload, headers=headers)
        data = await response.json()

        if not data:
            return await ctx.send(embed=discord.Embed(color=standards.error_color,
                                                      title=f"{standards.error_emoji} __**ERROR**__",
                                                      description='Dieser Spieler existiert nicht.'))
        uuid = data[0]['id']

        url_history = url_history_str.format(uuid)

        async with session.get(url_history) as resp:
            data_json = await resp.json()
        embed = discord.Embed(color=standards.normal_color, title=f"Namehistory from {Name}",
                              description=f"UUID: `{uuid}`")
        for data in data_json:
            try:
                time_int = int(str(data['changedToAt'])[:-3])
                changedToAt = datetime.datetime.fromtimestamp(time_int).strftime("%d %B %Y")
            except:
                changedToAt = "Orginaler Name:"
            embed.add_field(name=f"`{data['name']}`", value=changedToAt)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Public(bot))
