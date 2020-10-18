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
        helpText: list = self.helpText[ctx.command.full_parent_name.lower().split(' ')[0]].copy()
        return discord.Embed(color=std.error_color, title=f'**__Command Hilfe__**', description=f'**{text}**\n\n' + "\n".join(helpText).format(p=ctx.prefix))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error):
        lang = await ctx.lang()

        if hasattr(ctx.command, "on_error") or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error")):
            return

        if isinstance(error, commands.BadArgument) or isinstance(error, commands.BadUnionArgument):
            if isinstance(error, commands.RoleNotFound):
                return await ctx.error(lang["roleNotFound"])
            if isinstance(error, commands.MemberNotFound):
                return await ctx.error(lang["memberNotFound"])
            if isinstance(error, commands.UserNotFound):
                return await ctx.error(lang["userNotFound"])
            if isinstance(error, commands.ChannelNotFound):
                return await ctx.error(lang["channelNotFound"])
            else:
                await ctx.error(lang["badArgument"].format(e=str(error)))

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.error(lang["missingArgument"].format(p=str(error.param.name)))

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.error(lang["botMissingPermissions"].format(p=" ".join(error.missing_perms)))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.error(lang["userMissingPermissions"].format(p=" ".join(error.missing_perms)))

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CommandOnCooldown):
            cooldown = error.cooldown
            await ctx.error(lang["cooldownCommand"].format(p=str(cooldown.per), r=str(cooldown.rate), rt=str(round(error.retry_after))))

        elif isinstance(error, commands.NotOwner):
            await ctx.error(lang["ownerOnly"])

        elif isinstance(error, commands.DisabledCommand):
            await ctx.error(lang["disabledCommand"])

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            error = error.__cause__
            if isinstance(error, discord.Forbidden):
                try:
                    await ctx.error(lang["discordForbidden"])
                except:
                    pass

            else:
                userEmbed = discord.Embed(color=std.error_color, title=f"{std.error_emoji} **__ERROR__**")
                userEmbed.add_field(name="Original Error", value=f'```py{error}```')
                try:
                    await ctx.send(embed=userEmbed)
                except Exception as e:
                    self.bot.logger.exception(f'Error\n{type(e).__name__}: {e}')
                    channel = self.bot.get_guild(694790265382109224).get_channel(718554837771616316)
                    embed = discord.Embed(color=discord.Color.red())
                    embed.add_field(name=ctx.guild.name,
                                    value=ctx.command.name)
                    embed.add_field(name='Error',
                                    value=f'{type(error).__name__}: {error}')
                    return await channel.send(embed=embed)

                if self.bot.user.id == 505433541916622850:
                    if ctx.cog.qualified_name == 'Owner':
                        return

                    channel = self.bot.get_guild(694790265382109224).get_channel(718554837771616316)
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
