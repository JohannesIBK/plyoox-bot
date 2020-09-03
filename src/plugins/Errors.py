import asyncio
import codecs
import json

import discord
from discord.ext import commands

import main
from utils.ext import standards as std, context


class Errors(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.helpText = json.load(codecs.open(r'utils/json/help_de.json', encoding='utf-8'))

    async def _help(self, ctx: context.Context, text = None):
        helpText: list = self.helpText[ctx.command.name.lower()].copy()

        embed: discord.Embed = discord.Embed(color=std.error_color, title=f'**__Command Hilfe__**',
                                             description=f'**{text}**\n\n' + "\n".join(helpText).format(p=ctx.prefix))
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error):
        if hasattr(ctx.command, "on_error") or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error")):
            return

        if isinstance(error, commands.BadArgument) or isinstance(error, commands.BadUnionArgument):
            embed = await self._help(ctx, f'Ein Argument wurde falsch angegeben.')
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = await self._help(ctx, f'Das Argument `{error.param.name}` wurde nicht angegeben.')
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=std.getErrorEmbed(f'Dem Bot fehlt die Berechtigung(en) {" ".join(error.missing_perms)}'))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=std.getErrorEmbed(f'Dir fehlen die Berechtigung(en) `{" ".join(error.missing_perms)}`.'))

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CommandOnCooldown):
            cooldown = error.cooldown
            await ctx.send(embed=std.getErrorEmbed(f'Dieser Command hat einen Cooldown. '
                                                   f'Du kannst ihn nur {cooldown.rate} pro {cooldown.per}s benutzen.\n'
                                                   f'Versuche es in {round(error.retry_after)}s erneut.'))

        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=std.getErrorEmbed('Diesen Command kann nur der Owner des Bots ausführen.'))

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=std.getErrorEmbed('Dieser Command ist auf diesem Server deaktiviert.'))

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            error = error.__cause__
            if isinstance(error, discord.Forbidden):
                try:
                    await ctx.send(embed=std.getErrorEmbed('Der Bot hat keine Berechtigung um den Command auszuführen.'))
                except:
                    pass

            elif isinstance(error, asyncio.TimeoutError):
                await ctx.send(embed=std.getErrorEmbed('Dein Report wurde abgebrochen, da du zu lange gebraucht hast.'))

            else:
                userEmbed = discord.Embed(color=std.error_color, title=f"{std.error_emoji} **__ERROR__**")
                userEmbed.add_field(name="Original Error", value=f'{error}')
                try:
                    await ctx.send(embed=userEmbed)
                except Exception as e:
                    self.bot.logger.exception(f'Error\n{type(e).__name__}: {e}')
                    channel: discord.TextChannel = self.bot.get_guild(694790265382109224).get_channel(718554837771616316)
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
