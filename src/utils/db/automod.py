import discord


class Base:
    __slots__ = ('sid', 'state', 'points', 'whitelist', 'bot')

    sid: int
    state: int
    points: int
    whitelist: list[int]


class Invites(Base):
    __slots__ = 'partner'

    partner: list[int]

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.partner = []
            self.points = 0
        else:
            self.state = record.get('invitestate')
            self.points = record.get('invitepoints')
            self.whitelist = record.get('invitewhitelist') or []
            self.partner = record.get('invitepatner') or []

    async def reload(self, record=None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT sid, invitepartner, invitewhitelist, invitepoints, invitestate '
                'FROM automod.automod WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.partner = []
            self.points = 0
        else:
            self.state = record.get('invitestate')
            self.points = record.get('invitepoints')
            self.whitelist = record.get('invitewhitelist') or []
            self.partner = record.get('invitepatner') or []


class Blacklist(Base):
    __slots__ = 'words'

    words: list[str]

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.words = []
            self.points = 0
        else:
            self.state = record.get('blackliststate')
            self.points = record.get('blacklistpoints')
            self.whitelist = record.get('blacklistwhitelist') or []
            self.words = record.get('blacklistwords') or []

    async def reload(self, record=None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT sid, blacklistpoints, blackliststate, blacklistwhitelist, blacklistwords '
                'FROM automod.automod WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.words = []
        else:
            self.state = record.get('blackliststate')
            self.points = record.get('blacklistpoints')
            self.whitelist = record.get('blacklistwhitelist') or []
            self.words = record.get('blacklistwords') or []


class Caps(Base):
    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.points = 0
        else:
            self.state = record.get('capsstate')
            self.points = record.get('capspoints')
            self.whitelist = record.get('capswhitelist') or []

    async def reload(self, record=None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT capspoints, capsstate, capswhitelist FROM automod.automod WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
        else:
            self.state = record.get('capsstate')
            self.points = record.get('capspoints')
            self.whitelist = record.get('capswhitelist') or []


class Links(Base):
    __slots__ = ('links', 'iswhitelist')

    links: list[str]
    iswhitelist: bool

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.links = []
            self.iswhitelist = False
            self.points = 0
        else:
            self.state = record.get('linksstate')
            self.points = record.get('linkspoints')
            self.whitelist = record.get('linkswhitelist') or []
            self.links = record.get('linkslinks') or []
            self.iswhitelist = record.get('linksiswhitelist')

    async def reload(self, record=None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT linksiswhitelist, linkslinks, linkspoints, linksstate, linkswhitelist '
                'FROM automod.automod WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.links = []
            self.iswhitelist = False
            self.points = 0
        else:
            self.state = record.get('linksstate')
            self.points = record.get('linkspoints')
            self.whitelist = record.get('linkswhitelist') or []
            self.links = record.get('linkslinks') or []
            self.iswhitelist = record.get('linksiswhitelist')


class Mentions(Base):
    __slots__ = ('count', 'everyone')

    count: int
    everyone: bool

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.count = 5
            self.everyone = False
            self.points = 0
        else:
            self.state = record.get('mentionsstate')
            self.points = record.get('mentionspoints')
            self.whitelist = record.get('mentionswhitelist') or []
            self.count = record.get('mentionscount')
            self.everyone = record.get('mentionseveryone')

    async def reload(self, record=None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT mentionscount, mentionseveryone, mentionspoints, mentionsstate, '
                'mentionswhitelist FROM automod.automod WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.count = 5
        else:
            self.state = record.get('mentionsstate')
            self.points = record.get('mentionspoints')
            self.whitelist = record.get('mentionswhitelist') or []
            self.count = record.get('mentionscount')
            self.everyone = record.get('mentionseveryone')


class Config:
    __slots__ = (
        'sid', 'logchannelID', 'gmm', 'maxpoints', 'action', 'modroles', 'logging',
        'mutetime', 'bantime', 'ignoredroles', 'helperroles', 'bot', '_muterole'
    )

    sid: int
    logchannelID: int
    gmm: bool
    maxpoints: int
    action: int
    modroles: list[int]
    logging: bool
    mutetime: int
    bantime: int
    ignoredroles: list[int]
    helperroles: list[int]
    _muterole: int

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot
        if record is None:
            self.ignoredroles = []
            self.helperroles = []
            self.logchannelID = None
            self.gmm = False
            self.maxpoints = 0
            self.action = 0
            self.logchannelID = None
            self.bantime = 86400
            self.mutetime = 86400
            self.modroles = []
            self._muterole = None
        else:
            self.logchannelID = record.get('logchannel')
            self.gmm = record.get('gmm')
            self.maxpoints = record.get('maxpoints')
            self.action = record.get('action')
            self.logging = record.get('logging')
            self.bantime = record.get('bantime')
            self.mutetime = record.get('mutetime')
            self.ignoredroles = record.get('ignoredroles') or []
            self.helperroles = record.get('helperroles') or []
            self.modroles = record.get('modroles') or []
            self._muterole = record.get('muterole')

    @property
    def logchannel(self) -> discord.TextChannel:
        guild = self.bot.get_guild(self.sid)
        return guild and guild.get_channel(self.logchannelID)

    @property
    def muterole(self):
        guild = self.bot.get_guild(self.sid)
        return guild and guild.get_role(self._muterole)

    async def reload(self):
        record = await self.bot.db.fetchrow('SELECT * FROM automod.config WHERE sid = $1', self.sid)
        if record is None:
            self.ignoredroles = []
            self.helperroles = []
            self.logchannelID = None
            self.gmm = False
            self.maxpoints = 0
            self.action = 0
            self.logchannelID = None
            self.bantime = 86400
            self.mutetime = 86400
            self.modroles = []
            self._muterole = None
        else:
            self.logchannelID = record.get('logchannel')
            self.gmm = record.get('gmm')
            self.maxpoints = record.get('maxpoints')
            self.action = record.get('action')
            self.logchannelID = record.get('logging')
            self.bantime = record.get('bantime')
            self.mutetime = record.get('mutetime')
            self.ignoredroles = record.get('ignoredroles') or []
            self.helperroles = record.get('helperroles') or []
            self.modroles = record.get('modroles') or []


class Automod:
    __slots__ = ('config', 'invites', 'mentions', 'caps', 'links', 'blacklist', 'bot', 'sid')

    sid: int
    config: Config
    invites: Invites
    mentions: Mentions
    caps: Caps
    links: Links
    blacklist: Blacklist

    def __init__(self, bot, sid, record):
        self.bot = bot
        self.sid = sid
        self.config = Config(bot, record, sid)
        self.blacklist = Blacklist(bot, record, sid)
        self.links = Links(bot, record, sid)
        self.invites = Invites(bot, record, sid)
        self.caps = Caps(bot, record, sid)
        self.mentions = Mentions(bot, record, sid)

    async def reload(self):
        record = await self.bot.db.fetchrow(
            'SELECT * FROM automod.automod WHERE sid = $1', self.sid)
        await self.config.reload(),
        await self.blacklist.reload(record),
        await self.links.reload(record),
        await self.invites.reload(record),
        await self.caps.reload(record),
        await self.mentions.reload(record)
