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

        if not await self.bot.get(msg.guild.id, 'leveling'):
            return

        author: discord.Member = msg.author
        guild: discord.Guild = msg.guild
        key: str = f'{author.id}{guild.id}'
        userRoles: list = [role.id for role in author.roles]

        noXPChannels: list = await self.bot.get(guild.id, 'noxpchannels')
        if noXPChannels:
            if msg.channel.id in noXPChannels:
                return

        noXPRole: list = await self.bot.get(guild.id, 'noxprole')
        if noXPRole in userRoles:
            return

        userData = await self.bot.db.fetchrow("SELECT xp, guildid, time FROM extra.levels WHERE id = $1", key)
        if not userData:
            return await self.bot.db.execute(
                "INSERT INTO extra.levels (userid, guildid, xp, time, id) VALUES ($1, $2, $3, $4, $5)",
                author.id, guild.id, random.randint(15, 25), time.time(), key)

        # if time.time() - userData['time'] < 60:
        #     return
        newXP = random.randint(15, 25)
        await self.bot.db.execute("UPDATE extra.levels SET xp = xp + $1, time = $2 WHERE id = $3", newXP, time.time(), key)

        currentLvl = self._get_level_from_xp(userData['xp'])
        nextLvl = self._get_level_from_xp(userData['xp'] + newXP)
        if currentLvl >= nextLvl:
            data = await self.bot.db.fetchrow("SELECT channel, roles, message, remove FROM config.leveling WHERE sid = $1", guild.id)
            if data is None:
                return

            if data['roles']:
                roles = data['roles']
                roles.sort(key = lambda role: role[1])
                if data['remove']:
                    role = list(filter(lambda role: role[1] == nextLvl, roles)) or None
                    removeRoles = list(filter(lambda role: role[1] != nextLvl, roles)) or None
                    if not role:
                        return
                    await author.add_roles(guild.get_role(role[0][0]))
                    if removeRoles:
                        await author.remove_roles(*[guild.get_role(role[0]) for role in removeRoles])
                else:
                    addLvlRoles = []
                    for role in data['roles']:
                        if role[0] not in userRoles and role[1] <= nextLvl:
                            addLvlRoles.append(guild.get_role(role[0]))
                    await author.add_roles(*addLvlRoles)

            lvlMsg = data['message']
            channel = guild.get_channel(data['channel'])
            lvlMsg = formatMessage(lvlMsg, author, nextLvl)
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

        if user.bot:
            return await ctx.send(embed=std.getEmbed('Bots können keine XP erhalten!'))

        userData = await ctx.db.fetchrow("SELECT xp FROM extra.levels WHERE id = $1", f'{user.id}{ctx.guild.id}')
        if not userData:
            return await ctx.send(embed=std.getErrorEmbed('Dieser User hat noch nie etwas geschrieben.'))

        lvl = self._get_level_from_xp(userData['xp'])
        lvlXP = self._get_level_xp(lvl)
        if lvl == 0:
            currentXP = userData['xp']
        else:
            currentXP = userData['xp'] - self._get_xp_from_lvl(lvl - 1)

        embed = discord.Embed(color=user.color, title=f"**{user.display_name}**")
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=f"{std.level_emoji} Level", value=str(lvl))
        embed.add_field(name=f"{std.booster4_emoji} XP", value=f"{currentXP}/{lvlXP}")
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
        users = await ctx.db.fetch('SELECT * FROM extra.levels WHERE guildid = $1 ORDER BY xp DESC LIMIT 15', ctx.guild.id)

        embed = discord.Embed(color=std.normal_color, title='TOP 10')
        count = 0

        for userData in users:
            if userData['xp'] == 0:
                continue

            lvl = self._get_level_from_xp(userData['xp'])
            lvlXP = self._get_level_xp(lvl)
            if lvl == 0:
                currentXP = userData['xp']
            else:
                currentXP = userData['xp'] - self._get_xp_from_lvl(lvl - 1)

            member: discord.Member = self.bot.get_user(userData['userid'])
            if member is None:
                continue

            count += 1
            if count == 11:
                break

            embed.add_field(name=f"{count}. {member.display_name}", value=f'Level: {lvl}\nXP: {currentXP}/{lvlXP}')
        await ctx.send(embed=embed)

    @cmd(aliases=["rl"])
    @checks.isMod()
    @checks.isActive('leveling')
    async def resetlevel(self, ctx, user: discord.Member):
        await ctx.db.execute("DELETE FROM extra.levels WHERE id = $1", f'{user.id}{ctx.guild.id}')
        await ctx.send(embed=std.getEmbed(f'{std.law_emoji} Das Level des Users {user} wurde erfolgreich zurückgesetzt.'))


def setup(bot):
    bot.add_cog(Leveling(bot))
