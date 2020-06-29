import random
import time

import discord
from discord.ext import commands

from utils.ext import checks, standards


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_levels_xp(self, lvl):
        xp = 0
        for _ in range(1, lvl):
            xp += self._get_level_xp(lvl + 1)

        return xp

    @staticmethod
    def _get_level_xp(n):
        return 5 * (n ** 2) + 50 * n + 100

    def _get_level_from_xp(self, xp):
        remaining_xp = int(xp)
        level = 0

        while remaining_xp >= self._get_level_xp(level):
            remaining_xp -= self._get_level_xp(level)
            level += 1

        return level

    # --------------------------------listeners--------------------------------

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        if msg.guild is None:
            return

        if not isinstance(msg.author, discord.Member):
            return

        if not await self.bot.db.fetchval("SELECT leveling FROM config.modules WHERE sid = $1", msg.guild.id):
            return

        authorid = msg.author.id
        guildid = msg.guild.id

        user = await self.bot.db.fetchrow("SELECT xp, guildid, lvl, time FROM extra.levels WHERE id = $1 ",
                                          f'{authorid}{guildid}')

        data = await self.bot.db.fetchrow("SELECT noxp FROM config.leveling WHERE sid = $1", guildid)

        if msg.author.roles and data['noxp']:
            if data['noxp'] in [role.id for role in msg.author.roles]:
                return

        if not user:
            return await self.bot.db.execute(
                "INSERT INTO extra.levels (userid, guildid, lvl, xp, time, id) VALUES ($1, $2, 0, 0, 0, $3)",
                authorid, guildid, f'{authorid}{guildid}')

        if time.time() - user['time'] < 60:
            return

        xp = user['xp'] + random.randint(15, 25)
        await self.bot.db.execute("UPDATE extra.levels SET xp = $1, time = $2 WHERE id = $3", xp, time.time(),
                                  f'{authorid}{guildid}')

        needed_xp = self._get_level_xp(user["lvl"])
        current_xp = user["xp"]

        if current_xp >= needed_xp:
            await self.bot.db.execute("UPDATE extra.levels SET lvl = $1, xp = $2 WHERE id = $3",
                                      user["lvl"] + 1, current_xp - needed_xp, f'{authorid}{guildid}')

            data = await self.bot.db.fetchrow("SELECT channel, roles, message FROM config.leveling WHERE sid = $1",
                                              msg.guild.id)

            channel = msg.guild.get_channel(data['channel'])
            lvl_msg = data['message']

            if data['roles']:
                mind = min([role for role in data['roles'] if user["lvl"] + 1 >= role[1]] or [(0, None)])

                if mind is not None:

                    try:
                        await msg.author.add_roles(msg.guild.get_role(mind[0]))
                    except:
                        pass

            if lvl_msg is None:
                return

            if channel is not None:
                await channel.send(lvl_msg.format(user=msg.author, userm=msg.author.mention, lvl=user["lvl"] + 1))

            else:
                await msg.channel.send(lvl_msg.format(user=msg.author, userm=msg.author.mention, lvl=user["lvl"] + 1))

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        xp_role = await self.bot.db.fetchval("SELECT noxp FROM config.leveling WHERE sid = $1", role.guild.id)
        roles = await self.bot.db.fetchval("SELECT roles FROM config.leveling WHERE sid = $1", role.guild.id)

        if role.id == xp_role:
            await self.bot.db.execute("UPDATE config.leveling SET noxp = NULL WHERE sid = $1", role.guild.id)

        elif roles is not None:
            for lvl_role in roles:
                if lvl_role[0] == role.id:
                    await self.bot.db.execute(
                        "UPDATE config.leveling SET roles = array_remove(roles, $1) WHERE sid = $2", lvl_role,
                        role.guild.id)
                    break

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        old_channel = await self.bot.db.fetchval("SELECT channel FROM config.leveling WHERE sid = $1", channel.guild.id)

        if old_channel == channel.id:
            await self.bot.db.execute("UPDATE config.leveling SET channel = NULL WHERE sid = $1", channel.guild.id)

    # --------------------------------commands--------------------------------

    @commands.command(aliases=['rank'])
    @checks.isActive('leveling')
    async def level(self, ctx, User: discord.Member = None):
        if User is None:
            User = ctx.author

        userid = User.id
        guildid = ctx.guild.id

        user = await ctx.db.fetchrow("SELECT * FROM extra.levels WHERE id = $1", f'{userid}{guildid}')

        if not user:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="__**ERROR**__",
                                                      description='Dieser User hat noch nie etwas geschrieben.'))

        xp = user['xp']
        lvl = user['lvl']

        if xp == 0 and lvl == 0:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="__**ERROR**__",
                                                      description='Du bist noch nicht geranked! Erreiche Level 1 um dein Ranking zu sehen.'))

        level_xp = self._get_level_xp(lvl)

        embed = discord.Embed(color=User.color, timestamp=ctx.message.created_at, title=f"**{User.display_name}**")
        embed.set_thumbnail(url=User.avatar_url)
        embed.add_field(name="Level", value=lvl)
        embed.add_field(name="XP", value=f"{xp}/{level_xp}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["top"])
    @checks.isActive('leveling')
    async def top10(self, ctx):
        def sort(user_):
            lvl_xp = self._get_levels_xp(user_["lvl"])
            return lvl_xp + user_["xp"]

        all_users = await ctx.db.fetch('SELECT * FROM extra.levels WHERE guildid = $1', ctx.guild.id)

        all_users.sort(key=sort, reverse=True)

        embed = discord.Embed(color=standards.normal_color, title='TOP 10')
        count = 0

        for user in all_users:
            discord_user = self.bot.get_user(user['userid'])

            if discord_user is None:
                continue

            lvl = user['lvl']
            xp = user['xp']

            if xp == 0 and lvl == 0:
                continue

            count += 1
            if count == 11:
                break

            level_xp = self._get_level_xp(lvl)

            embed.add_field(name=f"{count}. {discord_user}", value=f'Level: {lvl}\nXP: {xp}/{level_xp}', inline=True)
        await ctx.send(embed=embed)

    @commands.command(aliases=["rl"])
    @checks.isMod()
    @checks.isActive('leveling')
    async def resetlevel(self, ctx, User: discord.Member):
        await ctx.db.execute("DELETE FROM extra.levels WHERE id = $1", f'{User.id}{ctx.guild.id}')
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'Das Level des Users {User} wurde erfolgreich zurückgesetzt.'))

    @commands.command(aliases=["channel", "lvlc"])
    @checks.hasPerms(administrator=True)
    async def Levelchannel(self, ctx, Channel: discord.TextChannel = None):
        if Channel is None:
            await ctx.db.execute("UPDATE config.leveling SET channel = NULL WHERE sid = $2", ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description='Die Nachrichten werden nun in den jeweiligen Channel gesendet.'))

        else:
            perms = [perm for perm, value in ctx.me.permissions_in(Channel) if value]

            if 'send_messages' not in perms:
                return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                          description='Der Bot hat keine Berechtigung in diesen Channel zu schreiben.'))

            await ctx.db.execute("UPDATE config.leveling SET channel = $1 WHERE sid = $2", Channel.id, ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=f'Level-UP Nachrichten werden nun in {Channel.mention} geschickt.'))

    @commands.group(aliases=['rr'], case_insensitive=True, invoke_without_command=True)
    @commands.bot_has_permissions(manage_roles=True)
    @checks.isActive('leveling')
    async def rewardRole(self, ctx):
        await ctx.send("Bitte benutze das Webdashboard! http://plyoox.akajonas.xyz/")
    #     def sort(val):
    #         return int(str(val).split(".")[0])
    #
    #     rewards = await ctx.db.fetchval("SELECT roles FROM config.leveling WHERE sid = $1", ctx.guild.id)
    #     active_rewards = []
    #
    #     if rewards:
    #         for reward in rewards:
    #             str_str = reward.split(".")
    #             role = ctx.guild.get_role(int(str_str[1]))
    #             if role is not None:
    #                 active_rewards.append(reward)
    #             else:
    #                 await ctx.db.execute("UPDATE config.leveling SET roles = array_remove(roles, $1) WHERE sid = $2",
    #                                      reward, ctx.guild.id)
    #
    #         if active_rewards:
    #             active_rewards.sort(key=sort)
    #             rewards_str = ""
    #             for i in active_rewards:
    #                 lst = str(i).split(".")
    #                 rewards_str += f'**Level:** {lst[0]} | **Rolle:** {ctx.guild.get_role(int(lst[1])).mention}\n'
    #             embed = discord.Embed(color=standards.normal_color)
    #             embed.add_field(name='Rollen-Belohnungen', value=rewards_str)
    #             await ctx.send(embed=embed)
    #
    #         else:
    #             return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                       description='Der Server hat keine Rollen-Rewards.'))
    #
    #     else:
    #         return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                   description='Der Server hat keine Rollen-Rewards.'))
    #
    # @rewardRole.command()
    # @checks.has_permissions(administrator=True)
    # async def add(self, ctx, Level: int, *, Role: discord.Role):
    #     if Level > 100:
    #         return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
    #                                                   description='Das maximale Level ist 100.'))
    #
    #     if not checks.bot_over(ctx, Role) or Role.managed:
    #         return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                   description='Der Bot hat keine Berechtigung diese Rolle zu vergeben.'))
    #
    #     data = await ctx.db.fetchrow("SELECT * FROM config.leveling WHERE sid = $1", ctx.guild.id)
    #     rewards = data['roles']
    #
    #     role_ids = []
    #     levels = []
    #
    #     if rewards:
    #         for x in rewards:
    #             lst = x.split('.')
    #             role_ids.append(int(lst[1]))
    #             levels.append(int(lst[0]))
    #
    #         if Role.id in role_ids:
    #             return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                       description='Diese Rolle ist bereits eine Belohnung.'))
    #
    #         if len(rewards) > 10:
    #             return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                       description='Der Server darf maximal 10 Rewards besitzen.'))
    #
    #         if Level in levels:
    #             return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                       description='Dieses Level ist bereits eine Belohnung.'))
    #
    #     str_lvl = {'%s.%s' % (Level, Role.id)}
    #
    #     await ctx.db.execute("UPDATE config.leveling set roles = roles || $1 WHERE sid = $2", str_lvl, ctx.guild.id)
    #     await ctx.send(embed=discord.Embed(color=standards.normal_color,
    #                                        description=f'Die Rolle {Role.mention} ist nun ein Reward für Level {Level}.'))
    #
    # @rewardRole.command()
    # @checks.has_permissions(administrator=True)
    # async def remove(self, ctx, Level: int, *, Role: discord.Role):
    #     rewards = await ctx.db.fetchval("SELECT roles FROM config.leveling WHERE sid = $1", ctx.guild.id)
    #     str_lvl = f'{Level}.{Role.id}'
    #
    #     if not rewards:
    #         return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                   description='Der Server hat keine Rollen-Rewards.'))
    #
    #     if str_lvl not in rewards:
    #         return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
    #                                                   description='Dieser Reward existiert nicht.'))
    #
    #     await ctx.db.execute("UPDATE config.leveling SET roles = array_remove(roles, $1) WHERE sid = $2", str_lvl,
    #                          ctx.guild.id)
    #     await ctx.send(embed=discord.Embed(color=standards.normal_color,
    #                                        description='Der Reward wurde entfernt.'))

    @commands.command(aliases=["noxp"])
    @checks.hasPerms(administrator=True)
    async def noxprole(self, ctx, Role: discord.Role = None):
        if Role is None:
            await ctx.db.execute("UPDATE config.leveling SET noxp = NULL WHERE sid = $1", ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description='v'))

        else:
            if not ctx.me.top_role > Role:
                return await ctx.send(embed=discord.Embed(color=standards.error_color,
                                                          description='Der Bot hat keine Berechtigung diese Rolle zu vergeben.'))

            await ctx.db.execute("UPDATE config.leveling SET noxp = $1 WHERE sid = $2", Role.id, ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=f'Die Rolle {Role.mention} bekommt nun kein XP mehr.'))

    @commands.command(aliases=['message'])
    @checks.hasPerms(administrator=True)
    async def levelmessage(self, ctx, *, Message):
        if Message is None:
            await ctx.db.execute("UPDATE config.leveling SET message = NULL WHERE sid = $1", ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description='Die Nachricht wurde entfernt. User erhalten nun keine Nachricht mehr wenn sie ein Level aufsteigen.'))

        else:
            try:
                msg = Message.format(user=ctx.author, userm=ctx.author.mention, lvl=1)
            except KeyError:
                await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                   description='Verwende nur {user}, {userm} und {lvl}'))

            else:
                await ctx.db.execute("UPDATE config.leveling SET message = $1 WHERE sid = $2", Message, ctx.guild.id)
                await ctx.send(embed=discord.Embed(color=standards.normal_color, title=f'Level-Up Nachricht',
                                                   description=msg))


def setup(bot):
    bot.add_cog(Leveling(bot))
