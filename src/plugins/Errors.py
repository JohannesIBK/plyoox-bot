import discord
from discord.ext import commands

import main
from utils.ext import standards as std, context


class Errors(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error):
        lang = await ctx.lang(module=self.qualified_name)

        if hasattr(ctx.command, "on_error") or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error")):
            return

        if isinstance(error, commands.BadArgument) or isinstance(error, commands.BadUnionArgument):
            if isinstance(error, commands.RoleNotFound):
                return await ctx.error(lang["error.rolenotfound"].format(a=error.argument))
            if isinstance(error, commands.MemberNotFound):
                return await ctx.error(lang["error.membernotfound"].format(a=error.argument))
            if isinstance(error, commands.UserNotFound):
                return await ctx.error(lang["error.usernotfound"].format(a=error.argument))
            if isinstance(error, commands.ChannelNotFound):
                return await ctx.error(lang["error.channelnotfound"].format(a=error.argument))
            else:
                await ctx.error(lang["error.badargument"].format(e=str(error)))

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.error(lang["error.missingargument"].format(p=str(error.param.name)))

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.error(lang["error.permissions.bot"].format(p=" ".join(error.missing_perms)))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.error(lang["error.permissions.user"].format(p=" ".join(error.missing_perms)))

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CommandOnCooldown):
            cooldown = error.cooldown
            await ctx.error(lang["error.command.cooldown"].format(p=str(cooldown.per), r=str(cooldown.rate), rt=str(round(error.retry_after))))

        elif isinstance(error, commands.NotOwner):
            await ctx.error(lang["error.command.owneronly"])

        elif isinstance(error, commands.DisabledCommand):
            await ctx.error(lang["error.command.disabled"])

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            error = error.__cause__
            if isinstance(error, discord.Forbidden):
                try:
                    await ctx.error(lang["error.discord.forbidden"])
                except:
                    pass

            else:
                userEmbed = discord.Embed(color=std.error_color, title=f"{std.error_emoji} **__ERROR__**")
                userEmbed.add_field(name="Original Error", value=f'```py\n{error}```')
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
