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
    @checks.hasPerms(administrator=True)
    async def prefix(self, ctx, prefix: str):
        if len(prefix) > 3:
            return await ctx.send(embed=standards.getErrorEmbed('Der Prefix darf maximal 3 Zeichen lang sein.'))

        await ctx.db.execute("UPDATE config.guild SET prefix = $1 WHERE sid = $2", prefix, ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'prefix': prefix})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{standards.yes_emoji} Der Prefix wurde erfolgreich zu `{prefix}` geändert.'))

    @grp(case_insensitive=True)
    @checks.hasPerms(administrator=True)
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
    async def automod(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET automod = true WHERE sid = $1", ctx.guild.id)
        await self.bot.update_redis(ctx.guild.id, {'automod': True})
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der AutoMod wurde erfolgreich aktiviert."'))

    @activate.command()
    async def welcomer(self, ctx):
        await ctx.db.execute("UPDATE config.modules SET welcomer = true WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Welcomer wurde erfolgreich aktiviert."'))

    @grp(case_insensitive=True)
    @checks.hasPerms(administrator=True)
    async def deactivate(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @deactivate.command(name='leveling')
    @commands.bot_has_permissions(manage_roles=True)
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

    @cmd()
    @checks.hasPerms(administrator=True)
    async def rules(self, ctx):
        await ctx.message.delete()
        msg = rules.rules
        await ctx.send(msg)

    @cmd()
    @checks.hasPerms(administrator=True)
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


def setup(bot):
    bot.add_cog(Servermoderation(bot))
