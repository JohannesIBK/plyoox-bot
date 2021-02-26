import random
import time
from datetime import datetime

import discord
from discord.ext import commands

import main
from utils.ext import checks
from utils.ext import context
from utils.ext import standards as std
from utils.ext.cmds import cmd
from utils.ext.formatter import formatMessage


class Leveling(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @staticmethod
    def _get_xp_from_lvl(lvl: int):
        xp = 100
        for _ in range(1, lvl + 1):
            xp += Leveling._get_level_xp(_)
        return xp

    @staticmethod
    def _get_level_xp(lvl):
        return 5 * (lvl ** 2) + 50 * lvl + 100

    @staticmethod
    def _get_level_from_xp(xp: int):
        level = 0
        while xp >= Leveling._get_level_xp(level):
            xp -= Leveling._get_level_xp(level)
            level += 1
        return level

    # --------------------------------listeners--------------------------------

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if msg.guild is None:
            return

        if not isinstance(msg.author, discord.Member):
            return

        guild_config = await self.bot.cache.get(msg.guild.id)
        if guild_config is None or not guild_config.modules.leveling:
            return
        config = guild_config.leveling

        author = msg.author
        guild = msg.guild
        user_roles = [role.id for role in author.roles]

        if msg.channel.id in config.noxpchannelIDs:
            return

        if config.noxproleID in user_roles:
            return

        user_data = await self.bot.db.fetchrow(
            'SELECT xp, sid, time, id FROM extra.levels WHERE uid = $1 and sid = $2',
            author.id, guild.id)
        if not user_data:
            return await self.bot.db.execute(
                "INSERT INTO extra.levels (uid, sid, xp, time) VALUES ($1, $2, $3, $4)",
                author.id, guild.id, random.randint(15, 25), time.time())

        if time.time() - user_data['time'] < 60:
            return

        new_xp = random.randint(15, 25)
        await self.bot.db.execute(
            "UPDATE extra.levels SET xp = xp + $1, time = $2 WHERE id = $3",
            new_xp, time.time(), user_data['id'])

        before_lvl = self._get_level_from_xp(user_data['xp'])
        current_lvl = self._get_level_from_xp(user_data['xp'] + new_xp)
        if current_lvl > before_lvl:
            add_role = None

            roles = config.roles
            add_role_id = list(filter(lambda role: role[1] == current_lvl, roles))

            if add_role_id:
                add_role = guild.get_role(add_role_id[0][0])

            roles.sort(key=lambda role: role[1])

            if config.remove:
                if not add_role:
                    return

                remove_roles = list(filter(lambda role: role[1] != current_lvl, roles)) or None
                await author.add_roles(add_role)
                if remove_roles:
                    await author.remove_roles(*[guild.get_role(role[0]) for role in remove_roles if
                                                guild.get_role(role[0])])
            else:
                add_lvl_roles = []
                for role in roles:
                    if role[0] not in user_roles and role[1] <= current_lvl:
                        new_role = guild.get_role(role[0])
                        if new_role:
                            add_lvl_roles.append(new_role)
                await author.add_roles(*add_lvl_roles)

            lvl_msg = formatMessage(config.message, author, current_lvl, add_role)
            if lvl_msg is not None:
                if config.channelID == 0:
                    await msg.channel.send(lvl_msg)
                elif config.channelID == 1:
                    await msg.author.send(lvl_msg)
                elif config.channelID is not None:
                    await config.channel.send(lvl_msg)

    # --------------------------------commands--------------------------------

    @cmd(aliases=['rank'])
    @checks.isActive('leveling')
    async def level(self, ctx: context.Context, user: discord.Member = None):
        lang = await ctx.lang()

        if user is None:
            user = ctx.author

        if user.bot:
            return await ctx.error(lang["level.error.bot"])

        user_data = await ctx.db.fetchrow(
            "WITH users AS (SELECT xp, uid, row_number() OVER (ORDER BY xp DESC) "
            "AS count FROM extra.levels WHERE sid = $1) SELECT * FROM users WHERE uid = $2",
            ctx.guild.id, user.id)
        if not user_data:
            return await ctx.error(lang["level.error.noentry"])

        lvl = self._get_level_from_xp(user_data['xp'])
        lvl_xp = self._get_level_xp(lvl)
        if lvl == 0:
            current_xp = user_data['xp']
        else:
            current_xp = user_data['xp'] - self._get_xp_from_lvl(lvl - 1)

        embed = discord.Embed(color=user.color,
                              timestamp=datetime.utcnow())
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=std.arrow + lang["level.embed.level.name"], value=f'```{lvl}```')
        embed.add_field(name=std.arrow + lang["level.embed.xp.name"],
                        value=f"```{current_xp}/{lvl_xp}```")
        embed.add_field(name=std.arrow + lang["level.embed.rank.name"],
                        value=f'```#{user_data["count"]}```')
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('leveling')
    async def levelRoles(self, ctx: context.Context):
        lang = await ctx.lang()

        data = await self.bot.db.fetchval(
            "SELECT roles FROM config.leveling WHERE sid = $1",
            ctx.guild.id)

        if data is None:
            return await ctx.error(lang["levelroles.error.noroles"])

        lvl_roles = []
        for roleData in data:
            role = ctx.guild.get_role(roleData[0])
            lvl_roles.append([role, roleData[1]])
        lvl_roles.sort(key=lambda lvlRole: lvlRole[1])

        embed = discord.Embed(
            color=std.normal_color,
            title=lang["levelroles.embed.title"],
            description='\n'.join(f'{lvlRole[0].mention} | {lvlRole[1]}' for lvlRole in lvl_roles)
        )
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd(aliases=["top10"])
    @checks.isActive('leveling')
    async def top(self, ctx: context.Context):
        lang = await ctx.lang()

        users = await ctx.db.fetch(
            'SELECT * FROM extra.levels WHERE sid = $1 ORDER BY xp DESC LIMIT 15',
            ctx.guild.id)
        embed = discord.Embed(color=std.normal_color,
                              title=lang["top.embed.title"].format(g=ctx.guild.name))
        count = 0

        for userData in users:
            if userData['xp'] == 0:
                continue

            lvl = self._get_level_from_xp(userData['xp'])
            lvl_xp = self._get_level_xp(lvl)
            if lvl == 0:
                current_xp = userData['xp']
            else:
                current_xp = userData['xp'] - self._get_xp_from_lvl(lvl - 1)

            member = ctx.guild.get_member(userData['uid'])
            if member is None:
                continue

            count += 1
            if count == 11:
                break

            embed.add_field(name=f"{count}. {member.display_name}", value=std.quote(
                lang["top.embed.user.value"].format(l=lvl, c=current_xp, x=lvl_xp)))
        embed.set_footer(icon_url=ctx.author.avatar_url, text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    @cmd(aliases=["rl"])
    @checks.isMod()
    @checks.isActive('leveling')
    async def resetLevel(self, ctx: context.Context, user: discord.Member):
        lang = await ctx.lang()

        if user.bot:
            return await ctx.error(lang["resetlevel.error.bot"])
        await ctx.db.execute(
            "DELETE FROM extra.levels WHERE uid = $1 AND sid = $2",
            user.id, ctx.guild.id)
        await ctx.message.delete(delay=5)
        await ctx.embed(lang["resetlevel.message"].format(u=str(user)), delete_after=5)


def setup(bot):
    bot.add_cog(Leveling(bot))
