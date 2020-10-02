from typing import List

import discord


class Base:
    __slots__ = ('sid', 'state', 'points', 'whitelist', 'bot')

    sid: int
    state: int
    points: int
    _whitelist: List[int]

class Invites(Base):
    __slots__ = 'partner'

    partner: List[int]

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = 0
            self.whitelist = []
            self.partner = []
            self.points = None
        else:
            self.state = record['invitestate']
            self.points = record['invitepoints']
            self.whitelist = record['invitewhitelist'] or []
            self.partner = record['invitepatner'] or []

    async def reload(self, record = None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT sid, invitepatner, invitewhitelist, invitepoints, invitestate FROM automod.automod1 WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = None
            self.whitelist = []
            self.partner = []
            self.points = None
        else:
            self.state = record['invitestate']
            self.points = record['invitepoints']
            self.whitelist = record['invitewhitelist'] or []
            self.partner = record['invitepatner'] or []

class Blacklist(Base):
    __slots__ = 'words'

    words: List[str]

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = None
            self.whitelist = []
            self.words = []
            self.points = None
        else:
            self.state = record['blackliststate']
            self.points = record['blacklistpoints']
            self.whitelist = record['blacklistwhitelist'] or []
            self.words = record['blacklistwords'] or []

    async def reload(self, record = None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT sid, blacklistpoints, blackliststate, blacklistwhitelist, blacklistwords FROM automod.automod1 WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.words = []
        else:
            self.state = record['blackliststate']
            self.points = record['blacklistpoints']
            self.whitelist = record['blacklistwhitelist'] or []
            self.words = record['blacklistwords'] or []

class Caps(Base):
    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = None
            self.whitelist = []
            self.points = None
        else:
            self.state = record['capsstate']
            self.points = record['capspoints']
            self.whitelist = record['capswhitelist'] or []

    async def reload(self, record = None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT capspoints, capsstate, capswhitelist FROM automod.automod1 WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
        else:
            self.state = record['capsstate']
            self.points = record['capspoints']
            self.whitelist = record['capswhitelist'] or []

class Links(Base):
    __slots__ = ('links', 'iswhitelist')

    links: List[str]
    iswhitelist: bool

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = None
            self.whitelist = []
            self.links = []
            self.iswhitelist = None
            self.points = None
        else:
            self.state = record['linksstate']
            self.points = record['linkspoints']
            self.whitelist = record['linkswhitelist'] or []
            self.links = record['linkslinks'] or []
            self.iswhitelist = record['linksiswhitelist']

    async def reload(self, record = None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT linksiswhitelist, linkslinks, linkspoints, linksstate, linkswhitelist FROM automod.automod1 WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = None
            self.whitelist = []
            self.links = []
            self.iswhitelist = None
            self.points = None
        else:
            self.state = record['linksstate']
            self.points = record['linkspoints']
            self.whitelist = record['linkswhitelist'] or []
            self.links = record['linkslinks'] or []
            self.iswhitelist = record['linksiswhitelist']

class Mentions(Base):
    __slots__ = ('count', 'everyone')

    count: int
    everyone: bool

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot

        if record is None:
            self.state = None
            self.whitelist = []
            self.count = None
            self.everyone = None
            self.points = None
        else:
            self.state = record['mentionsstate']
            self.points = record['mentionspoints']
            self.whitelist = record['mentionswhitelist'] or []
            self.count = record['mentionscount']
            self.everyone = record['mentionseveryone']

    async def reload(self, record = None):
        if record is None:
            record = await self.bot.db.fetchrow(
                'SELECT mentionscount, mentionseveryone, mentionspoints, mentionsstate, mentionswhitelist FROM automod.automod1 WHERE sid = $1',
                self.sid)

        if record is None:
            self.state = 0
            self.whitelist = []
            self.count = 5
        else:
            self.state = record['mentionsstate']
            self.points = record['mentionspoints']
            self.whitelist = record['mentionswhitelist'] or []
            self.count = record['mentionscount']
            self.everyone = record['mentionseveryone']

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
    modroles: List[int]
    logging: bool
    mutetime: int
    bantime: int
    ignoredroles: List[int]
    helperroles: List[int]
    _muterole: int

    def __init__(self, bot, record, sid):
        self.sid = sid
        self.bot = bot
        if record is None:
            self.ignoredroles = []
            self.helperroles = []
            self.logchannelID = None
            self.gmm = None
            self.maxpoints = None
            self.action = None
            self.logchannelID = None
            self.bantime = None
            self.mutetime = None
            self.modroles = None
            self._muterole = None
        else:
            self.logchannelID = record['logchannel']
            self.gmm = record['gmm']
            self.maxpoints = record['maxpoints']
            self.action = record['action']
            self.logchannelID = record['logging']
            self.bantime = record['bantime']
            self.mutetime = record['mutetime']
            self.ignoredroles = record['ignoredroles'] or []
            self.helperroles = record['helperroles'] or []
            self.modroles = record['modroles'] or []
            self._muterole = record['muterole']

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
            self.gmm = None
            self.maxpoints = None
            self.action = None
            self.logchannelID = None
            self.bantime = None
            self.mutetime = None
            self.modroles = None
            self._muterole = None
        else:
            self.logchannelID = record['logchannel']
            self.gmm = record['gmm']
            self.maxpoints = record['maxpoints']
            self.action = record['action']
            self.logchannelID = record['logging']
            self.bantime = record['bantime']
            self.mutetime = record['mutetime']
            self.ignoredroles = record['ignoredroles'] or []
            self.helperroles = record['helperroles'] or []
            self.modroles = record['modroles'] or []


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
        self.config = Config(bot, record, sid),
        self.blacklist = Blacklist(bot, record, sid)
        self.links = Links(bot, record, sid)
        self.invites = Invites(bot, record, sid)
        self.caps = Caps(bot, record, sid)
        self.mentions = Mentions(bot, record, sid)

    async def reload(self):
        record = await self.bot.db.fetchrow('SELECT * FROM automod.automod1 WHERE sid = $1', self.sid)
        await self.config.reload(),
        await self.blacklist.reload(record),
        await self.links.reload(record),
        await self.invites.reload(record),
        await self.caps.reload(record),
        await self.mentions.reload(record)
