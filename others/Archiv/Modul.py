import discord
from discord.ext import commands

from utils.ext import checks, standards


class Modul(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_user_count.start()

    # --------------------------------commands--------------------------------

    @commands.group(case_insensitive=True)
    @checks.hasPerms(administartor=True)
    async def activate(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @activate.command()
    async def fun(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET funmodul = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['fun']))

    @activate.command()
    @commands.bot_has_permissions(manage_roles=True)
    async def leveling(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET levelsystem = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['leveling']))

    @activate.command()
    async def cmds(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET publictag = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['cogs']))

    @activate.command()
    @commands.bot_has_permissions(manage_channels=True)
    async def usercount(self, ctx):
        lang = await self.bot.lang(ctx)

        overwrite = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False, speak=False),
        }
        channel = await ctx.guild.create_voice_channel(name=f'User-Count: {len(ctx.guild.members)}', overwrites=overwrite)

        await ctx.db.fetch("UPDATE dcsettings SET usercount = $1 WHERE sid = $2", channel.id, ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['usercount']))

    @activate.command()
    async def chatlogging(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET msglogging = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['chatlogging']))

    @activate.command()
    async def ticket(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET ticketsystem = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['ticket']))

    @activate.command()
    async def minecraft(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET minecraftmodul = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['minecraft']))

    @activate.command()
    async def automod(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET automod = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['automod'].format(p=ctx.prefix)))

        self.bot.fast_db[ctx.guild.id]['automod'] = True

    @commands.group(case_insensitive=True)
    @checks.hasPerms(administartor=True)
    async def deactivate(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @deactivate.command(name='fun')
    async def _fun(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET funmodul = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name='leveling')
    @commands.bot_has_permissions(manage_roles=True)
    async def _leveling(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET levelsystem = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name='cogs')
    async def _cmds(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET publictag = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name='usercount')
    @commands.bot_has_permissions(manage_channels=True)
    async def _usercount(self, ctx):
        lang = await self.bot.lang(ctx)

        channel_id = await ctx.db.fetchval("SELECT usercount FROM dcsettings WHERE sid = $1", ctx.guild.id)
        channel = ctx.guild.get_channel(channel_id)

        if channel is not None:
            await channel.delete()

        await ctx.db.fetch("UPDATE dcsettings SET usercount = NULL WHERE sid = $1", ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name='chatlogging')
    async def _chatlogging(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET msglogging = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name="ticket")
    async def _ticket(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET ticketsystem = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name="minecraft")
    async def _minecraft(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET minecraftmodul = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @deactivate.command(name="automod")
    async def _automod(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET automod = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

        self.bot.fast_db[ctx.guild.id]['automod'] = False


def setup(bot):
    bot.add_cog(Modul(bot))
