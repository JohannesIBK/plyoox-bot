import discord
from discord.ext import commands


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        if len(argument) > 512:
            raise commands.BadArgument(f'Grund zu lang ({len(argument)}/512)')

        return argument


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            memberID = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=memberID))
            except discord.NotFound:
                raise commands.BadArgument('Dieser User ist nicht gebannt.') from None

        banList = await ctx.guild.bans()
        user = discord.utils.find(lambda u: str(u.user) == argument, banList)

        if user is None:
            raise commands.BadArgument('Dieser User ist nicht gebannt.')
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
                raise commands.UserNotFound
