import random
import time

import discord
from discord.ext import commands

import main
from utils.ext import checks, standards as std
from utils.ext.cmds import cmd
from utils.ext.formatter import formatMessage


class Leveling(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    def _get_levels_xp(self, lvl: int):
        if lvl == 0:
            return 0

        xp = 0
        for _ in range(0, lvl):
            xp += self._get_level_xp(lvl + 1)

        return xp

    @staticmethod
    def _get_level_xp(n):
        return 5 * (n ** 2) + 50 * n + 100

    def _get_level_from_xp(self, xp: int):
        remaining_xp = int(xp)
        level = 0
        while remaining_xp >= self._get_level_xp(level):
            remaining_xp -= self._get_level_xp(level)
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

        if not await self.bot.get(msg.guild.id, 'leveling'):
            return

        authorID: int = msg.author.id
        guildID: int = msg.guild.id
        key: str = f'{authorID}{guildID}'
        userRoles: list = [role.id for role in msg.author.roles]

        noXPChannels: list = await self.bot.get(guildID, 'noxpchannels')
        if noXPChannels:
            if msg.channel.id in noXPChannels:
                return

        noXPRole: list = await self.bot.get(guildID, 'noxprole')
        if noXPRole in userRoles:
            return

        userData = await self.bot.db.fetchrow(
            "SELECT xp, guildid, lvl, time FROM extra.levels WHERE id = $1",
            key)
        if not userData:
            return await self.bot.db.execute(
                "INSERT INTO extra.levels (userid, guildid, lvl, xp, time, id) VALUES ($1, $2, 0, 0, 0, $3)",
                authorID, guildID, key)

        if time.time() - userData['time'] < 60:
            return

        xp = userData['xp'] + random.randint(15, 25)
        await self.bot.db.execute(
            "UPDATE extra.levels SET xp = $1, time = $2 WHERE id = $3",
            xp, time.time(), key)

        neededXP: int = self._get_level_xp(userData["lvl"])
        currentXP: int = userData["xp"]
        if currentXP >= neededXP:
            await self.bot.db.execute(
                "UPDATE extra.levels SET lvl = $1, xp = $2 WHERE id = $3",
                userData["lvl"] + 1, currentXP - neededXP, key)

            data = await self.bot.db.fetchrow(
                "SELECT channel, roles, message FROM config.leveling WHERE sid = $1",
                msg.guild.id)

            if roles := data['roles']:
                addLvlRoles = []
                for role in roles:
                    if role[0] not in userRoles and role[1] <= userData["lvl"] + 1:
                        addLvlRoles.append(msg.guild.get_role(role[0]))

                await msg.author.add_roles(*addLvlRoles)

            lvlMsg = data['message']
            channel = msg.guild.get_channel(data['channel'])
            lvlMsg = formatMessage(lvlMsg, msg.author, userData["lvl"] + 1)
            if lvlMsg is not None:
                if channel is not None:
                    await channel.send(lvlMsg)
                else:
                    await msg.channel.send(lvlMsg)

    # --------------------------------commands--------------------------------

    @cmd(aliases=['rank'])
    @checks.isActive('leveling')
    async def level(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        userData = await ctx.db.fetchrow("SELECT * FROM extra.levels WHERE id = $1", f'{user.id}{ctx.guild.id}')
        if not userData:
            return await ctx.send(embed=std.getErrorEmbed('Dieser User hat noch nie etwas geschrieben.'))

        lvl = userData['lvl']
        lvlXP = self._get_level_xp(lvl)

        embed = discord.Embed(color=user.color, title=f"**{user.display_name}**")
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=f"{std.level_emoji} Level", value=lvl)
        embed.add_field(name=f"{std.booster4_emoji} XP", value=f"{userData['xp']}/{lvlXP}")
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('leveling')
    async def levelRoles(self, ctx):
        data = await self.bot.db.fetchval("SELECT roles FROM config.leveling WHERE sid = $1", ctx.guild.id)
        if data is None:
            return await ctx.send(embed=std.getErrorEmbed('Der Server hat keine Levelrollen festgelegt.'))

        lvlRoles = []
        for roleData in data:
            role = ctx.guild.get_role(roleData[0])
            lvlRoles.append([role, roleData[1]])
        await ctx.send(embed=discord.Embed(color=std.normal_color, title='Level-Rollen', description='\n'.join(f'{lvlRole[0].mention} | {lvlRole[1]}' for lvlRole in lvlRoles)))

    @cmd(aliases=["top10"])
    @checks.isActive('leveling')
    async def top(self, ctx):
        def sort(lvlUser):
            lvlXP = self._get_levels_xp(lvlUser["lvl"])
            return lvlXP + lvlUser["xp"]
        users = await ctx.db.fetch('SELECT * FROM extra.levels WHERE guildid = $1 ORDER BY lvl DESC LIMIT 15', ctx.guild.id)
        users.sort(key=sort, reverse=True)

        embed = discord.Embed(color=std.normal_color, title='TOP 10')
        count = 0

        for user in users:
            lvl = user['lvl']
            neededXP = self._get_level_xp(lvl)
            member = self.bot.get_user(user['userid'])
            if member is None:
                continue

            if user['xp'] == 0:
                continue

            count += 1
            if count == 11:
                break

            embed.add_field(name=f"{count}. {member}", value=f'Level: {lvl}\nXP: {user["xp"]}/{neededXP}')
        await ctx.send(embed=embed)

    @cmd(aliases=["rl"])
    @checks.isMod()
    @checks.isActive('leveling')
    async def resetlevel(self, ctx, user: discord.Member):
        await ctx.db.execute("DELETE FROM extra.levels WHERE id = $1", f'{user.id}{ctx.guild.id}')
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Das Level des Users {user} wurde erfolgreich zurückgesetzt.'))


def setup(bot):
    bot.add_cog(Leveling(bot))
