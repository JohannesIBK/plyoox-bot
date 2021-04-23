import discord
from discord.ext import commands

from utils.ext.context import Context


class ActionReason(commands.Converter):
    reason: str
    raw_reason: str

    async def convert(self, ctx: Context, argument):
        lang = await ctx.lang()
        if len(argument) > 510 - len(str(ctx.author)):
            raise commands.BadArgument(lang["converters.error.reasontolong"].format(a=str(len(argument)), m=str(len(str(ctx.author)))))

        reason = str(ctx.author) + ": " + argument
        self.reason = reason
        self.raw_reason = argument
        return self

    def __str__(self):
        return self.raw_reason


class BannedMember(commands.Converter):
    async def convert(self, ctx: Context, argument):
        lang = await ctx.lang()
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound as e:
                raise commands.BadArgument(lang["converters.notbanned"]) from e

        ban_list = await ctx.guild.bans()
        user = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

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
