import asyncio
from typing import Dict

from . import leveling, modules, automod


class GuildConfig:
    __slots__ = ('_leveling', '_automod', '_modules', '_prefix', 'sid', 'bot')

    _leveling: leveling.Leveling
    _automod: automod.Automod
    _modules: modules.Modules
    _prefix: str
    sid: int

    def __init__(self, bot, sid, records):
        self.sid = sid
        self.bot = bot
        self._prefix = records[0]
        self._automod = automod.Automod(self.bot, self.sid, records[1])
        self._leveling = leveling.Leveling(self.bot, self.sid, records[2])
        self._modules = modules.Modules(self.bot, self.sid, records[2])

    @property
    def prefix(self) -> list:
        prefixes = [f'<@{self.bot.user.id}', f'<@!{self.bot.user.id}']
        if self._prefix:
            prefixes.append(self._prefix)
        return prefixes

    @prefix.setter
    def prefix(self, prefix):
        self._prefix = prefix

    @property
    def automod(self) -> automod.Automod:
        return self._automod

    @property
    def leveling(self) -> leveling.Leveling:
        return self._leveling

    @property
    def modules(self) -> modules.Modules:
        return self._modules



class BotCache:
    __slots__ = 'bot'


    cache: Dict[int, GuildConfig] = {}

    def __init__(self, bot):
        self.bot = bot

    async def get(self, sid) -> GuildConfig:
        cache = self.cache.get(sid)
        if cache is None:

            # one request would take 2 seconds fml
            # please help
            part1 = await self.bot.db.fetchrow('SELECT sid, invitestate, invitepoints, invitewhitelist, invitepatner FROM automod.automod WHERE sid = $1', sid)
            part2 = await self.bot.db.fetchrow('SELECT linksstate, linkspoints, linkswhitelist, linksiswhitelist, linkslinks, mentionseveryone FROM automod.automod WHERE sid = $1', sid)
            part3 = await self.bot.db.fetchrow('SELECT mentionsstate, mentionspoints, mentionswhitelist, mentionscount, capspoints FROM automod.automod WHERE sid = $1', sid)
            part4 = await self.bot.db.fetchrow('SELECT capswhitelist, blacklistpoints, blacklistwhitelist, blacklistwords, capsstate, blackliststate FROM automod.automod WHERE sid = $1', sid)
            automodConfig = await self.bot.db.fetchrow('SELECT c.* FROM automod.config c WHERE c.sid = $1', sid)

            automodRecord = dict(automodConfig) if automodConfig else {}
            if part1:
                automodRecord.update(dict(part1))
                automodRecord.update(dict(part2))
                automodRecord.update(dict(part3))
                automodRecord.update(dict(part4))


            records = await self.bot.db.fetchrow('SELECT * FROM config.leveling l FULL JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1', sid)

            cache = GuildConfig(self.bot, sid, ['-', automodRecord or None, records])
            self.cache.update({ sid: cache })
        return cache

    async def set(self, sid):
        records = await asyncio.gather(*[
            self.bot.db.fetchval('SELECT prefix FROM config.guild WHERE sid = $1', sid),
            self.bot.db.fetchrow('SELECT c.*, a.* FROM automod.automod a FULL JOIN automod.config c ON a.sid = c.sid WHERE c.sid = $1', sid),
            self.bot.db.fetchrow('SELECT * FROM config.leveling l FULL JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1', sid),
        ])
        cache = GuildConfig(self.bot, sid, records)
        self.cache.update({sid: cache})

    def remove(self, sid):
        self.cache.pop(sid)



