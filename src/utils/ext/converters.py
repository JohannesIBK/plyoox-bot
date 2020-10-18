import time

import discord
from discord.ext import commands


class ParseTime(commands.Converter):
    async def convert(self, ctx, timeStr):
        if timeStr.endswith('y'):
            try:
                years = int(timeStr.replace('y', ''))
                if years != 1:
                    raise commands.BadArgument('Die Zeit ist zu groß/klein!')

                return years * 365 * 3600 * 24 + time.time()
            except ValueError as err:
                raise commands.BadArgument('Deine Eingabe war fehlerhaft.') from err

        elif timeStr.endswith('d'):
            try:
                days = int(timeStr.replace('d', ''))
                if days > 365 or days < 1:
                    raise commands.BadArgument('Die Zeit ist zu groß/klein!')

                return days * 3600 * 24 + time.time()
            except ValueError as err:
                raise commands.BadArgument('Deine Eingabe war fehlerhaft.') from err

        elif timeStr.endswith('h'):
            try:
                hours = float(timeStr.replace('h', ''))
                if hours > 48 or hours < 0.25:
                    raise commands.BadArgument('Die Zeit ist zu groß/klein!')

                return hours * 3600 + time.time()
            except ValueError as err:
                raise commands.BadArgument('Deine Eingabe war fehlerhaft.') from err

        elif timeStr.endswith('min'):
            try:
                mins = float(timeStr.replace('min', ''))
                if mins > 120 or mins < 15:
                    raise commands.BadArgument('Die Zeit ist zu groß/klein!')

                return mins * 60 + time.time()
            except ValueError as err:
                raise commands.BadArgument('Deine Eingabe war fehlerhaft.') from err
        else:
            raise commands.BadArgument('Deine Eingabe war fehlerhaft.') from None


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
