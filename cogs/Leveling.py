import random
import re

import time

import discord
from discord.ext import commands

import main
from utils.ext import checks, standards
from utils.ext.cmds import cmd

BRACKET_REGEX = r'{.*?}'


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

        user: discord.Member = msg.author
        authorID: int = msg.author.id
        guildID: int = msg.guild.id
        key: str = f'{authorID}{guildID}'

        noXPChannels: list = await self.bot.get(guildID, 'noxpchannels')
        if noXPChannels:
            if msg.channel.id in noXPChannels:
                return

        noXPRoles: list = await self.bot.get(guildID, 'noxproles')
        if msg.author.roles and noXPRoles:
            if any(role in noXPRoles for role in msg.author.roles):
                return

        userData = await self.bot.db.fetchrow("SELECT xp, guildid, lvl, time FROM extra.levels WHERE id = $1 ", key)
        if not userData:
            return await self.bot.db.execute(
                "INSERT INTO extra.levels (userid, guildid, lvl, xp, time, id) VALUES ($1, $2, 0, 0, 0, $3)",
                authorID, guildID, key)

        if time.time() - userData['time'] < 60:
            return

        xp = userData['xp'] + random.randint(15, 25)
        await self.bot.db.execute("UPDATE extra.levels SET xp = $1, time = $2 WHERE id = $3", xp, time.time(), key)

        neededXP: int = self._get_level_xp(userData["lvl"])
        currentXP: int = userData["xp"]

        if currentXP >= neededXP:
            await self.bot.db.execute("UPDATE extra.levels SET lvl = $1, xp = $2 WHERE id = $3",
                                      userData["lvl"] + 1, currentXP - neededXP, key)

            data = await self.bot.db.fetchrow("SELECT channel, roles, message FROM config.leveling WHERE sid = $1",
                                              msg.guild.id)

            userRoles: list = [role.id for role in msg.author.roles]

            if (roles := data['roles']):
                addLvlRoles = []

                for role in roles:
                    if role[0] not in userRoles and role[1] <= userData["lvl"] + 1:
                        addLvlRoles.append(msg.guild.get_role(role[0]))

                await msg.author.add_roles(*addLvlRoles)


            lvlMsg = data['message']

            if lvlMsg is None:
                return

            channel = msg.guild.get_channel(data['channel'])
            placeholders = re.findall(BRACKET_REGEX, lvlMsg)

            for placeholder in placeholders:
                if placeholder.lower() == '{userm}':
                    lvlMsg = lvlMsg.replace(placeholder, user.mention)
                elif placeholder.lower() == '{user}':
                    lvlMsg = lvlMsg.replace(placeholder, str(user))
                elif placeholder.lower() == '{lvl}':
                    lvlMsg = lvlMsg.replace(placeholder, str(userData["lvl"] + 1))

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

        userID = user.id
        guildID = ctx.guild.id

        userData = await ctx.db.fetchrow("SELECT * FROM extra.levels WHERE id = $1", f'{userID}{guildID}')

        if not userData:
            return await ctx.send(embed=standards.getErrorEmbed('Dieser User hat noch nie etwas geschrieben.'))

        xp = userData['xp']
        lvl = userData['lvl']

        if xp == 0 and lvl == 0:
            return await ctx.send(embed=standards.getErrorEmbed('Du bist noch nicht geranked! Erreiche Level 1 um dein Ranking zu sehen.'))

        lvlXP = self._get_level_xp(lvl)

        embed = discord.Embed(color=user.color, title=f"**{user.display_name}**")
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=f"{standards.level_emoji} Level", value=lvl)
        embed.add_field(name=f"{standards.booster4_emoji} XP", value=f"{xp}/{lvlXP}")
        await ctx.send(embed=embed)

    @cmd(aliases=["top10"])
    @checks.isActive('leveling')
    async def top(self, ctx):
        def sort(lvlUser):
            lvlXP = self._get_levels_xp(lvlUser["lvl"])
            return lvlXP + lvlUser["xp"]
        allUser = await ctx.db.fetch('SELECT * FROM extra.levels WHERE guildid = $1 ORDER BY lvl DESC LIMIT 15', ctx.guild.id)
        allUser.sort(key=sort, reverse=True)

        embed = discord.Embed(color=standards.normal_color, title='TOP 10')
        count = 0

        for user in allUser:
            userObj = self.bot.get_user(user['userid'])

            if userObj is None:
                continue

            lvl = user['lvl']
            xp = user['xp']

            if xp == 0 and lvl == 0:
                continue

            count += 1
            if count == 11:
                break

            lvlXp = self._get_level_xp(lvl)

            embed.add_field(name=f"{count}. {userObj}", value=f'Level: {lvl}\nXP: {xp}/{lvlXp}', inline=True)
        await ctx.send(embed=embed)

    @cmd(aliases=["rl"])
    @checks.isMod()
    @checks.isActive('leveling')
    async def resetlevel(self, ctx, user: discord.Member):
        await ctx.db.execute("DELETE FROM extra.levels WHERE id = $1", f'{user.id}{ctx.guild.id}')
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.law_emoji} Das Level des Users {user} wurde erfolgreich zurückgesetzt.'))


def setup(bot):
    bot.add_cog(Leveling(bot))
