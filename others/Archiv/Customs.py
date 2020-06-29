import random

import discord
from discord.ext import commands

from utils.ext import checks, standards


class Customs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------------listeners--------------------------------

    @commands.Cog.listener()
    async def on_voice_state_update(self, memb, before, after):
        if after.channel:
            data = await self.bot.db.fetchrow("SELECT customchannel, customrole FROM dcsettings WHERE sid = $1", memb.guild.id)

            Channel = data["customchannel"]
            Role = data["customrole"]
            if Role is None or Channel is None:
                return
            try:
                if after.channel.id == Channel:
                    Role = memb.guild.get_role(Role)
                    await memb.add_roles(Role, atomic=True)
                else:
                    Role = memb.guild.get_role(Role)
                    await memb.remove_roles(Role)
            except:
                pass
        else:
            data = await self.bot.db.fetchrow("SELECT customchannel, customrole FROM dcsettings WHERE sid = $1", memb.guild.id)
            Channel = data["customchannel"]
            if before.channel.id == Channel:
                Role = memb.guild.get_role(data["customrole"])
                try:
                    await memb.remove_roles(Role)
                except:
                    pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if role.id == await self.bot.db.fetchval("SELECT customrole FROM dcsettings WHERE sid = $1", role.guild.id):
            await self.bot.execute("UPDATE dcsettings SET customrole = NULL WHERE sid = $1", role.guild.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.id == await self.bot.db.fetchval("SELECT customchannel FROM dcsettings WHERE sid = $1", channel.guild.id):
            await self.bot.execute("UPDATE dcsettings SET customchannel = NULL WHERE sid = $1", channel.guild.id)

    # --------------------------------commands--------------------------------

    @commands.command(aliases=["CusR"])
    @checks.hasPerms(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def CustomRole(self, ctx, Role: discord.Role = None):
        lang = await self.bot.lang(ctx, extras=True)

        if Role is None:
            await ctx.db.execute("UPDATE dcsettings SET customrole = NULL WHERE sid = $1", ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['off']))

        else:
            if not ctx.top_role > Role:
                return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                          description=lang['error_add_role_perms']))

            await ctx.db.execute("UPDATE dcsettings SET customrole = $1 WHERE sid = $2", Role.id, ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['on'].format(mention=Role.mention)))

    @commands.command(aliases=["CusC"])
    @checks.hasPerms(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def CustomChannel(self, ctx, Channel: discord.VoiceChannel = None):
        lang = await self.bot.lang(ctx, extras=True)

        if Channel is None:
            await ctx.db.execute("UPDATE dcsettings SET customchannel = NULL WHERE sid = $1", ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['off']))

        else:
            await ctx.db.execute("UPDATE dcsettings SET customchannel = $1 WHERE sid = $2", Channel.id, ctx.guild.id)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['on'].format(channel=Channel.mention)))

    @commands.command()
    @checks.hasPerms(ban_members=True)
    async def move(self, ctx, Channel: discord.VoiceChannel, Channel2: discord.VoiceChannel):
        lang = await self.bot.lang(ctx, extras=True)

        moved = 0
        for memb in Channel.members:
            try:
                await memb.move_to(Channel2)
                moved += 1
            except discord.Forbidden:
                return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                          description=lang['error_no_perms']))

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['move_msg'].format(moved=moved, channel=Channel.mention, channel2=Channel2.mention)))

    @commands.command()
    @checks.hasPerms(ban_members=True)
    async def rmove(self, ctx, Anzahl: int, Channel: discord.VoiceChannel, Channel2: discord.VoiceChannel):
        lang = await self.bot.lang(ctx, extras=True)

        if Anzahl > len(Channel.members):
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="Error",
                                               description=lang['error_no_perms']))

        else:
            for i in range(0, Anzahl, 1):
                member = random.choice(Channel.members)
                try:
                    await member.move_to(Channel2)
                except discord.Forbidden:
                    await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                       description=lang['error_no_perms']))
                    break


def setup(bot):
    bot.add_cog(Customs(bot))
