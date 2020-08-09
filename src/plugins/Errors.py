import asyncio
import codecs
import json
import logging

import discord
from discord.ext import commands

import main
from utils.ext import standards

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.helpText = json.load(codecs.open(r'other/help_de.json', encoding='utf-8'))

    async def _help(self, ctx, text = None):
        if text is None:
            helpText = self.helpText[ctx.command.name.split(" ")[0]]
            del helpText[0]
        else:
            helpText = [text]

        embed: discord.Embed = discord.Embed(color=standards.error_color, title=f'**__Command Help__**',
                                             description="\n".join(helpText))
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error") or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error")):
            return

        if isinstance(error, commands.BadArgument):
            embed = await self._help(ctx, 'Ein Argument wurde falsch angegeben.')
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = await self._help(ctx, f'Das Argument `{error.param.name}` wurde nicht angegeben.')
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms_str = ""
            for perm in error.missing_perms:
                missing_perms_str += f' {perm},'

            await ctx.send(embed=standards.getErrorEmbed(f'Dem Bot fehlt die Berechtigung(en) {missing_perms_str[:-1]}'))

        elif isinstance(error, commands.MissingPermissions):
            if error.missing_perms[0] == "nr":
                await ctx.send(embed=standards.getErrorEmbed('Du musst ein Moderator sein, um den Command auszuführen.'))

            else:
                missing_perms_str = ""
                for perm in error.missing_perms:
                    missing_perms_str += f'{perm}, '

                await ctx.send(embed=standards.getErrorEmbed(f'Dir fehlen die Berechtigungen `{missing_perms_str[:-2]}`.'))

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CommandOnCooldown):
            retryAfter = error.retry_after
            cooldown = error.cooldown
            rate = cooldown.rate
            per = cooldown.per

            await ctx.send(embed=standards.getErrorEmbed(f'Dieser Command hat einen Cooldown. Du kannst ihn nur {rate} pro {per}s benutzen.\n'
                                                         f'Versuche es in {round(retryAfter)}s erneut.'))

        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=standards.getErrorEmbed('Diesen Command kann nur der Owner des Bots ausführen.'))

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=standards.getErrorEmbed('Dieser Command ist auf diesem Server deaktiviert.'))

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            error = error.__cause__
            if isinstance(error, discord.Forbidden):
                try:
                    await ctx.send(embed=standards.getErrorEmbed('Der Bot hat keine Berechtigung um den Command auszuführen.'))
                except:
                    pass

            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send(embed=standards.getErrorEmbed('Dein Report wurde abgebrochen, da du zu lange gebraucht hast.'))

            elif isinstance(error, TypeError):
                await ctx.send(embed=standards.getErrorEmbed('Ein Fehler bei deiner Eingabe ist aufgetreten. Bitte überprüfe deine Eingabe.'))

            else:
                userEmbed = discord.Embed(color=standards.error_color, title=f"{standards.error_emoji} **__ERROR__**")
                userEmbed.add_field(name="Original Error", value=f'{error}')
                try:
                    await ctx.send(embed=userEmbed)
                except Exception as e:
                    log.exception(f'Error\n{type(e).__name__}: {e}')
                    channel: discord.TextChannel = ctx.guild.get_channel(718554837771616316)
                    embed = discord.Embed(color=discord.Color.red())
                    embed.add_field(name=ctx.guild.name,
                                    value=ctx.command.name)
                    embed.add_field(name='Error',
                                    value=f'{type(error).__name__}: {error}')
                    await channel.send(embed=embed)

                if self.bot.user.id == 505433541916622850:
                    if ctx.cog.qualified_name == 'Owner':
                        return

                    channel: discord.TextChannel = self.bot.get_guild(694790265382109224).get_channel(718554837771616316)
                    embed = discord.Embed(color=discord.Color.red())
                    embed.add_field(name=ctx.guild.name,
                                    value=ctx.command.name)
                    embed.add_field(name='Error',
                                    value=f'{type(error).__name__}: {error}')
                    await channel.send(embed=embed)
        else:
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Errors(bot))
