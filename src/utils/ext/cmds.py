from discord.ext import commands


class CommandsExtension(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

        self.showHelp = kwargs.get('showHelp', True)
        if not isinstance(self.showHelp, bool):
            raise TypeError(f'Excepted type bool got type {type(self.showHelp)}')

        self.category = kwargs.get('category', None)
        self.help = kwargs.get('help', None)


def cmd(*args, **kwargs):
    return commands.command(*args, **kwargs, cls=CommandsExtension)


class GroupExtension(commands.Group):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

        self.showHelp = kwargs.get('showHelp', True)
        if not isinstance(self.showHelp, bool):
            raise TypeError(f'Excepted type bool got type {type(self.showHelp)}')

        self.category = kwargs.get('category', None)
        self.help = kwargs.get('help', None)


def grp(*args, **kwargs):
    return commands.group(*args, **kwargs, cls=GroupExtension)
