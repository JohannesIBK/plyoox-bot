import discord
from discord.ext import commands

import main
from utils import rules
from utils.ext import checks, standards
from utils.ext.cmds import grp, cmd


class Servermoderation(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd(name="prefix")
    @checks.isAdmin()
    async def prefix(self, ctx, prefix: str):
        if len(prefix) > 3:
            return await ctx.send(embed=standards.getErrorEmbed('Der Prefix darf maximal 3 Zeichen lang sein.'))

        await ctx.db.execute("UPDATE config.guild SET prefix = $1 WHERE sid = $2", prefix, ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'prefix': prefix})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.yes_emoji} Der Prefix wurde erfolgreich zu `{prefix}` geändert.'))

    @grp(case_insensitive=True)
    @checks.isAdmin()
    async def activate(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @activate.command()
    @commands.bot_has_permissions(manage_roles=True)
    async def leveling(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET leveling = true WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'leveling': True})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Das Levelsystem wurde erfolgreich aktiviert.'))

    @activate.command()
    async def games(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET fun = true WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Das Games-Modul wurde erfolgreich aktiviert.'))

    @activate.command()
    @commands.bot_has_permissions(ban_members=True, kick_members=True, manage_roles=True, manage_messages=True)
    async def automod(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET automod = true WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'automod': True})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der AutoMod wurde erfolgreich aktiviert."'))

    @activate.command()
    @commands.bot_has_permissions()
    async def welcomer(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET welcomer = true WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Welcomer wurde erfolgreich aktiviert."'))

    @activate.command()
    @commands.bot_has_permissions(ban_members=True)
    async def globalbans(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET globalbans = true WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Globalbans wurden erfolgreich aktiviert."'))

    @grp(case_insensitive=True)
    @checks.isAdmin()
    async def deactivate(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @deactivate.command(name='leveling')
    async def _leveling(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET leveling = false WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'leveling': False})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Das Levelsystem wurde deaktiviert.'))

    @deactivate.command(name='games')
    async def _games(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET fun = false WHERE sid = $1", ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Das Games-Modul wurde deaktiviert'))

    @deactivate.command(name="automod")
    async def _automod(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET automod = false WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'automod': False})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Automod wurde deaktiviert'))

    @deactivate.command(name='welcomer')
    async def _welcomer(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET welcomer = false WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Welcomer wurde erfolgreich deaktiviert."'))

    @deactivate.command(name='globalbans')
    async def _globalban(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET globalbans = false WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Globalbans wurden erfolgreich deaktiviert."'))

    @cmd()
    @checks.isAdmin()
    async def rules(self, ctx):
        await ctx.message.delete()
        msg = rules.rules
        await ctx.send(msg)

    @cmd()
    @checks.isAdmin()
    async def rules1(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(color=0xc90c0c)
        embed.add_field(name="**__Regeln des Discord Servers__**",
                        value="Im folgenden Text werden die Regeln des Discords aufgelistet.\n**Beim Betreten des Servers stimmt man automatisch den Regeln zu.**")
        embed.add_field(name="__§1.1 | Discord-Guidelines__",
                        value="**»** Die **[Discord Nutzungsbedingungen](https://discordapp.com/terms)** und die **[Discord Community-Richtlinien](https://discordapp.com/guidelines)** müssen befolgt werden. Bei einem Verstoß gegen diese, wird der Account dem Discord Trust and Safety Team gemeldet.")
        embed.add_field(name="__§2.1 | Verhalten auf dem Discord__",
                        value="**»** Seid gegenüber jeder Person respektvoll. Behandlt jeden so, wie man selbst behandelt werden will.")
        embed.add_field(name="__§2.2 | Verhalten in den Chats__",
                        value="**»** Jeglicher Art von Spam (Mention, Caps, Emoji, …) ist verboten.\n**»** Jegliche Arten von Beleidigungen sind verboten.\n**»** NSFW-Content ist verboten.\n**»** Rassistische, sexistische, radikale, diskriminierende und ethisch inkorrekte Aussagen, Bilder und Videos sind verboten.")
        embed.add_field(name="__§3.1 | Verbreitung von Links, Bildern und Dateien__",
                        value="**»** Das Verbreiten von schädlichen Links, Bildern, Texten, Dateien oder Ähnlichem ist in jeglicher Form verboten.\n**»** Jegliche Programme, egal ob schädlich oder nicht, sind unerwünscht und können gelöscht werden. ")
        embed.add_field(name="__§3.2 | Verbreitung von Werbung__",
                        value="**»** Jegliche Art von Werbung, ob für einen Eigennutzen oder Nutzen für einen anderen, ist auf dem Discord verboten. Dazu zählt die Verbreitung in Chats, Avataren, Namen und sonstigen Medien.")
        embed.add_field(name="__§3.3 | Verbreitung von privaten Daten__",
                        value="**»** Private Daten sollte privat bleiben. Telefonnummern, Adressen, E-Mails und Ähnliches sind privat zu halten und nicht öffentlich zu teilen.")
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
    async def setupMute(self, ctx):
        guild: discord.Guild = ctx.guild

        muteRoleID: int = await ctx.db.fetchval('SELECT muterole FROM automod.config WHERE sid = $1', guild.id)
        muteRole: discord.Role = guild.get_role(muteRoleID)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Die Muterolle muss über der höchsten Rolle sein, die gemuted werden soll.'))
        await muteRole.edit(permissions=discord.Permissions.none())

        if muteRole is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Server hat keine Mute-Rolle!'))

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

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Die Muterolle wurde eingestellt.'))

    @cmd()
    @checks.isAdmin()
    async def lockGuild(self, ctx):
        guild: discord.Guild = ctx.guild

        await ctx.send('Start')

        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.permissions_synced:
                    continue

                overwrites = channel.overwrites
                newOverwrites = {}
                for overwriteObject, overwrite in overwrites.items():
                    if not isinstance(overwriteObject, discord.Role):
                        continue

                    overwrite.read_messages = False
                    overwrite.send_messages = False
                    newOverwrites.update({overwriteObject: overwrite})
                await channel.edit(overwrites=newOverwrites)

            elif isinstance(channel, discord.VoiceChannel):
                if channel.permissions_synced:
                    continue

                overwrites = channel.overwrites
                newOverwrites = {}
                for overwriteObject, overwrite in overwrites.items():
                    if not isinstance(overwriteObject, discord.Role):
                        continue

                    overwrite.view_channel = False
                    overwrite.speak = False
                    overwrite.stream = False
                    newOverwrites.update({overwriteObject: overwrite})
                await channel.edit(overwrites=newOverwrites)


            elif isinstance(channel, discord.CategoryChannel):
                overwrites = channel.overwrites
                newOverwrites = {}
                for overwriteObject, overwrite in overwrites.items():
                    if not isinstance(overwriteObject, discord.Role):
                        continue

                    overwrite.read_messages = False
                    overwrite.view_channel = False
                    overwrite.send_messages = False
                    overwrite.speak = False
                    overwrite.stream = False
                    newOverwrites.update({overwriteObject: overwrite})
                await channel.edit(overwrites=newOverwrites)

        await ctx.send('Setup')


def setup(bot):
    bot.add_cog(Servermoderation(bot))
