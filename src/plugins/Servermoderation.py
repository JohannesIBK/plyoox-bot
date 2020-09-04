import discord
from discord.ext import commands

import main
from utils import rules
from utils.ext import checks, standards as std, context
from utils.ext.cmds import grp, cmd


class Servermoderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd(name="prefix")
    @checks.isAdmin()
    async def prefix(self, ctx: context.Context, prefix: str):
        if len(prefix) > 3:
            return await ctx.error('Der Prefix darf maximal 3 Zeichen lang sein.')

        await ctx.db.execute("UPDATE config.guild SET prefix = $1 WHERE sid = $2", prefix, ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'prefix': prefix})
        await ctx.embed(f'{std.yes_emoji} Der Prefix wurde erfolgreich zu `{prefix}` geändert.')

    @grp(case_insensitive=True)
    @checks.isAdmin()
    async def activate(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @activate.command()
    @commands.bot_has_permissions(manage_roles=True)
    async def leveling(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET leveling = true WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'leveling': True})
        await ctx.embed('Das Levelsystem wurde erfolgreich aktiviert.')

    @activate.command()
    async def fun(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET fun = true WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Das Games-Modul wurde erfolgreich aktiviert.')

    @activate.command()
    @commands.bot_has_permissions(ban_members=True, kick_members=True, manage_roles=True, manage_messages=True)
    async def automod(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET automod = true WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'automod': True})
        await ctx.embed('Der AutoMod wurde erfolgreich aktiviert."')

    @activate.command()
    @commands.bot_has_permissions()
    async def welcomer(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET welcomer = true WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Der Welcomer wurde erfolgreich aktiviert."')

    @activate.command()
    @commands.bot_has_permissions(ban_members=True)
    async def globalbans(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET globalbans = true WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Globalbans wurden erfolgreich aktiviert.')

    @activate.command()
    @commands.bot_has_permissions(ban_members=True)
    async def logging(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET logging = true WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Logging wurden erfolgreich aktiviert.')

    @activate.command()
    @commands.bot_has_permissions(ban_members=True)
    async def timer(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET timers = true WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Timer wurden erfolgreich aktiviert.')

    @grp(case_insensitive=True)
    @checks.isAdmin()
    async def deactivate(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @deactivate.command(name='leveling')
    async def _leveling(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET leveling = false WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'leveling': False})
        await ctx.embed('Das Levelsystem wurde deaktiviert.')

    @deactivate.command(name='fun')
    async def _fun(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET fun = false WHERE sid = $1", ctx.guild.id)

        await ctx.embed('Das Fun-Modul wurde deaktiviert')

    @deactivate.command(name="automod")
    async def _automod(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET automod = false WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'automod': False})
        await ctx.embed('Der Automod wurde deaktiviert')

    @deactivate.command(name='welcomer')
    async def _welcomer(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET welcomer = false WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Der Welcomer wurde erfolgreich deaktiviert.')

    @deactivate.command(name='globalbans')
    async def _globalban(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET globalbans = false WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Globalbans wurden erfolgreich deaktiviert."')

    @deactivate.command(name='logging')
    async def _globalban(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET logging = false WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Logging wurden erfolgreich deaktiviert.')

    @deactivate.command(name='timer')
    async def _timer(self, ctx: context.Context):
        await ctx.db.execute("UPDATE config.modules SET logging = false WHERE sid = $1", ctx.guild.id)
        await ctx.embed('Timer wurden erfolgreich deaktiviert.')

    @cmd()
    @checks.isAdmin()
    async def rules(self, ctx: context.Context):
        await ctx.message.delete()
        msg = rules.rules
        await ctx.send(msg)

    @cmd()
    @checks.isAdmin()
    async def rules1(self, ctx: context.Context):
        await ctx.message.delete()
        embed = discord.Embed(color=0xc90c0c)
        embed.add_field(name="**__Regeln des Discord Servers__**",
                        value="Im folgenden Text werden die Regeln des Discords aufgelistet.\n**Beim Betreten des Servers stimmt man automatisch den Regeln zu.**")
        embed.add_field(name="__§1.1 | Discord-Guidelines__",
                        value="**»** Die **[Discord Nutzungsbedingungen](https://discordapp.com/terms)** und die **[Discord Community-Richtlinien](https://discordapp.com/guidelines)** müssen befolgt werden. Bei einem Verstoß gegen diese, wird der Account dem Discord Trust and Safety Team gemeldet.")
        embed.add_field(name="__§2.1 | Verhalten auf dem Discord__",
                        value="**»** Seid gegenüber jeder Person respektvoll. Behandelt jeden so, wie ihr selbst behandelt werden wollt.")
        embed.add_field(name="__§2.2 | Verhalten in den Chats__",
                        value="**»** Jeglicher Art von Spam (Mention, Caps, Emoji, …) ist verboten.\n**»** Jegliche Arten von Beleidigungen sind verboten.\n**»** NSFW-Content ist verboten.\n**»** Rassistische, sexistische, radikale, diskriminierende und ethisch inkorrekte Aussagen, Bilder und Videos sind verboten.")
        embed.add_field(name="__§3.1 | Verbreitung von Links, Bildern und Dateien__",
                        value="**»** Das Verbreiten von schädlichen Links, Bildern, Texten, Dateien oder Ähnlichem ist in jeglicher Form verboten.\n**»** Jegliche Programme, egal ob schädlich oder nicht, sind unerwünscht und können gelöscht werden. ")
        embed.add_field(name="__§3.2 | Verbreitung von Werbung__",
                        value="**»** Jegliche Art von Werbung, ob für einen Eigennutzen oder Nutzen für einen anderen, ist auf dem Discord verboten. Dazu zählt die Verbreitung in Chats, Avataren, Namen und sonstigen Medien.")
        embed.add_field(name="__§3.3 | Verbreitung von privaten Daten__",
                        value="**»** Private Daten sollen privat bleiben. Telefonnummern, Adressen, E-Mails und ähnliches sind privat zu halten und nicht öffentlich zu teilen.")
        embed.add_field(name="__§3.4 | Handel und Geschäfte__",
                        value="**»** Der Handel mit jeglichen Dingen ist auf dem Discord untersagt. Geschäfte und Handel sind privat zu regeln. ")
        embed.add_field(name="__§4.1 |  Nickname, Profilbild, Spieleanzeige__",
                        value="**»** Nicknamen, Spieleanzeigen und Profilbilder dürfen weder beleidigend, rassistisch, sexistisch, radikal, diskriminierend oder ethisch inkorrekt sein.")
        embed.add_field(name="__§5.1 | Sonstiges - Ausnahmen__",
                        value="**»** Falls eine Änderung der Regeln für einen bestimmten Channel existiert, kann man dies in der Channelbeschreibung finden.")
        embed.add_field(name="__§5.2 | Sonstiges - Selbstverständlichkeit__",
                        value="**»** Selbstverständliche Regeln müssen eingehalten werden, auch ohne, dass sie in diesem Regelwerk erwähnt werden")
        embed.add_field(name="__§5.3 | Sonstiges - Moderatoren__",
                        value="**»** Moderatoren haben immer Recht. Kein Moderator muss sein Handeln vor einem User rechtfertigen. ")
        embed.set_footer(text="by JohannesIBK")
        await ctx.send(embed=embed)

    @cmd()
    @checks.isAdmin()
    @commands.cooldown(1, 900, type=commands.BucketType.guild)
    @commands.bot_has_permissions(manage_channels=True)
    async def setupMute(self, ctx: context.Context):
        guild: discord.Guild = ctx.guild

        muteRoleID: int = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', guild.id)
        muteRole: discord.Role = guild.get_role(muteRoleID)
        if muteRole is None:
            return await ctx.error('Der Server hat keine Mute-Rolle!')

        await muteRole.edit(permissions=discord.Permissions.none())

        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_synced:
                    continue

                overwrite = discord.PermissionOverwrite.from_pair(
                    deny=discord.Permissions(2112),
                    allow=discord.Permissions(0))
                await channel.set_permissions(muteRole, overwrite=overwrite)

            if isinstance(channel, discord.VoiceChannel):
                if channel.permissions_synced:
                    continue

                overwrite = discord.PermissionOverwrite.from_pair(
                    deny=discord.Permissions(permissions=2097664),
                    allow=discord.Permissions(permissions=0))
                await channel.set_permissions(muteRole, overwrite=overwrite)

            if isinstance(channel, discord.CategoryChannel):
                overwrite = discord.PermissionOverwrite.from_pair(
                    deny=discord.Permissions(permissions=2099776),
                    allow=discord.Permissions(permissions=0))
                await channel.set_permissions(muteRole, overwrite=overwrite)

        await ctx.embed('Die Muterolle wurde eingestellt.')

    @cmd()
    @checks.isAdmin()
    async def copyblacklist(self, ctx: context.Context, guildID: int, overwrite: bool = False):
        guild: discord.Guild = ctx.bot.get_guild(guildID)
        if guild is None:
            return await ctx.error('Der Server konnte nicht gefunden werden.')
        member = guild.get_member(ctx.author.id)
        if member is None or not member.guild_permissions.administrator:
            return await ctx.error('Du bist nicht auf diesem Server oder hast keine Administrator-Rechte.')

        words = await ctx.db.fetchval(
            'SELECT words FROM automod.blacklist WHERE sid = $1',
            guild.id)

        if words is None:
            return await ctx.error('Der Server hat keine Wörter eingespeichert.')


        if overwrite:
            await ctx.db.execute(
                'UPDATE automod.blacklist SET words = $1 WHERE sid = $2',
                words, ctx.guild.id)
        else:
            await ctx.db.execute(
                'UPDATE automod.blacklist SET words = array_cat(words, $1) WHERE sid = $2',
                words, ctx.guild.id)


    # @cmd()
    # @checks.isAdmin()
    # @commands.bot_has_permissions(administrator=True)
    # async def lockGuild(self, ctx: context.Context):
    #     guild: discord.Guild = ctx.guild
    #
    #     await ctx.embed('Channel werden geschlossen...')
    #
    #     for channel in guild.channels:
    #         if isinstance(channel, discord.TextChannel):
    #             if channel.permissions_synced:
    #                 continue
    #
    #             overwrites = channel.overwrites
    #             newOverwrites = {}
    #             for overwriteObject, overwrite in overwrites.items():
    #                 if not isinstance(overwriteObject, discord.Role):
    #                     continue
    #
    #                 overwrite.read_messages = False
    #                 overwrite.send_messages = False
    #                 newOverwrites.update({overwriteObject: overwrite})
    #             await channel.edit(overwrites=newOverwrites)
    #
    #         elif isinstance(channel, discord.VoiceChannel):
    #             if channel.permissions_synced:
    #                 continue
    #
    #             overwrites = channel.overwrites
    #             newOverwrites = {}
    #             for overwriteObject, overwrite in overwrites.items():
    #                 if not isinstance(overwriteObject, discord.Role):
    #                     continue
    #
    #                 overwrite.view_channel = False
    #                 overwrite.speak = False
    #                 overwrite.stream = False
    #                 newOverwrites.update({overwriteObject: overwrite})
    #             await channel.edit(overwrites=newOverwrites)
    #
    #
    #         elif isinstance(channel, discord.CategoryChannel):
    #             overwrites = channel.overwrites
    #             newOverwrites = {}
    #             for overwriteObject, overwrite in overwrites.items():
    #                 if not isinstance(overwriteObject, discord.Role):
    #                     continue
    #
    #                 overwrite.read_messages = False
    #                 overwrite.view_channel = False
    #                 overwrite.send_messages = False
    #                 overwrite.speak = False
    #                 overwrite.stream = False
    #                 newOverwrites.update({overwriteObject: overwrite})
    #             await channel.edit(overwrites=newOverwrites)
    #
    #     await ctx.embed('Channel wurden geschlossen')


def setup(bot):
    bot.add_cog(Servermoderation(bot))
