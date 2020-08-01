import time

from discord.ext import commands


class ParseTime(commands.Converter):
    async def convert(self, ctx, timeStr):
        if timeStr.endswith('y'):
            try:
                years = int(timeStr.replace('d', ''))
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