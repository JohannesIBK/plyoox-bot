import asyncio

from . import leveling, modules, automod


class GuildConfig:
    __slots__ = ('_language', '_leveling', '_automod', '_modules', '_prefix', 'sid', 'bot')

    _leveling: leveling.Leveling
    _automod: automod.Automod
    _modules: modules.Modules
    _prefix: str
    _language: str
    sid: int

    def __init__(self, bot, sid, records):
        self.sid = sid
        self.bot = bot

        if records[0] is not None:
            self._prefix = records[0]["prefix"]
            self._language = records[0]["lang"]

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
    def lang(self) -> str:
        return self._language or "en"

    @lang.setter
    def lang(self, lang):
        self._language = lang

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

    cache: dict[int, GuildConfig] = {}
    fetching: list[int] = []

    def __init__(self, bot):
        self.bot = bot

    async def get(self, sid) -> GuildConfig:
        cache = self.cache.get(sid)
        if cache is None:
            if sid in self.fetching:
                for _ in range(20):
                    print(self.fetching)
                    data = self.cache.get(sid)
                    if data is not None:
                        return data

                    await asyncio.sleep(.20)
                return None

            self.fetching.append(sid)

            # one request would take 2 seconds fml
            # please help
            part1, part2, part3, part4, automodConfig, settings = await asyncio.gather(*[
                self.bot.db.fetchrow('SELECT sid, invitestate, invitepoints, invitewhitelist, invitepatner FROM automod.automod WHERE sid = $1', sid),
                self.bot.db.fetchrow('SELECT linksstate, linkspoints, linkswhitelist, linksiswhitelist, linkslinks, mentionseveryone FROM automod.automod WHERE sid = $1', sid),
                self.bot.db.fetchrow('SELECT mentionsstate, mentionspoints, mentionswhitelist, mentionscount, capspoints FROM automod.automod WHERE sid = $1', sid),
                self.bot.db.fetchrow('SELECT capswhitelist, blacklistpoints, blacklistwhitelist, blacklistwords, capsstate, blackliststate FROM automod.automod WHERE sid = $1', sid),
                self.bot.db.fetchrow('SELECT c.* FROM automod.config c WHERE c.sid = $1', sid),
                self.bot.db.fetchrow('SELECT prefix, lang FROM config.guild WHERE sid = $1', sid)
            ])

            automodRecord = dict(automodConfig) if automodConfig else {}
            if part1:
                automodRecord.update(dict(part1))
                automodRecord.update(dict(part2))
                automodRecord.update(dict(part3))
                automodRecord.update(dict(part4))

            records = await self.bot.db.fetchrow('SELECT * FROM config.leveling l FULL JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1', sid)

            cache = GuildConfig(self.bot, sid, [settings, automodRecord or None, records])
            self.cache.update({ sid: cache })
            self.fetching.remove(sid)

        return cache

    async def set(self, sid):
        records = await asyncio.gather(*[
            self.bot.db.fetchrow('SELECT prefix, lang FROM config.guild WHERE sid = $1', sid),
            self.bot.db.fetchrow('SELECT c.*, a.* FROM automod.automod a FULL JOIN automod.config c ON a.sid = c.sid WHERE c.sid = $1', sid),
            self.bot.db.fetchrow('SELECT * FROM config.leveling l FULL JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1', sid),
        ])
        cache = GuildConfig(self.bot, sid, records)
        self.cache.update({sid: cache})

    def remove(self, sid):
        self.cache.pop(sid)



