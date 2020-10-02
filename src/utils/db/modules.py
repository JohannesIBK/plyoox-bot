class Modules:
    __slots__ = ('fun', 'automod', 'leveling', 'logging', 'welcomer', 'globalbans', 'timers', 'commands', 'sid', 'bot')

    fun: bool
    automod: bool
    leveling: bool
    logging: bool
    welcomer: bool
    globalbans: bool
    commands: bool
    timers: bool
    sid: int

    def __init__(self, bot, sid, record):
        self.sid = sid
        self.bot = bot
        if record is not None:
            self.automod = record.get('automod')
            self.fun = record.get('fun')
            self.leveling = record.get('leveling')
            self.welcomer = record.get('welcomer')
            self.timers = record.get('timers')
            self.commands = record.get('commands')
            self.globalbans = record.get('globalbans')
            self.logging = record.get('logging')
        else:
            self.automod = False
            self.fun = False
            self.welcomer = False
            self.leveling = False
            self.logging = False
            self.globalbans = False
            self.commands = False
            self.timers = False

    async def reload(self, record = None):
        if not record:
            record = await self.bot.db.fetchrow('SELECT * FROM config.modules WHERE sid = $1', self.sid)
        if record is not None:
            self.automod = record['automod']
            self.fun = record['fun']
            self.leveling = record['leveling']
            self.welcomer = record['welcomer']
            self.timers = record['timers']
            self.commands = record['commands']
            self.globalbans = record['globalbans']
            self.logging = record['logging']
