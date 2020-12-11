import discord
from discord.ext import commands

from utils.ext.context import Context


class ActionReason(commands.Converter):
    async def convert(self, ctx: Context, argument):
        lang = await ctx.lang()
        if len(argument) > 510 - len(str(ctx.author)):
            raise commands.BadArgument(lang["converters.error.reasontolong"].format(a=str(len(argument)), m=str(len(str(ctx.author)))))

        argument = str(ctx.author) + ": " + argument
        return argument


class BannedMember(commands.Converter):
    async def convert(self, ctx: Context, argument):
        lang = await ctx.lang()
        if argument.isdigit():
            memberID = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=memberID))
            except discord.NotFound as e:
                raise commands.BadArgument(lang["converters.notbanned"]) from e

        banList = await ctx.guild.bans()
        user = discord.utils.find(lambda u: str(u.user) == argument, banList)

        if user is None:
            raise commands.BadArgument(lang["converters.notbanned"])
        return user


class AdvancedMember(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.UserConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                user_id = int(argument, base=10)
                return await ctx.bot.fetch_user(user_id)
            except (ValueError, discord.NotFound):
                raise commands.UserNotFound(argument)
