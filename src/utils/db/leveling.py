from typing import List


class Leveling:
    __slots__ = ('sid', 'channelID', 'message', 'noxpchannelIDs', 'noxproleID', 'remove', 'bot', 'roles')

    sid: int
    channelID: int
    message: str
    noxpchannelIDs: List[int]
    noxproleID: int
    remove: bool
    roles: List[list]

    def __init__(self, bot, sid, record):
        self.sid = sid
        self.bot = bot
        if record is None:
            self.roles = []
            self.noxpchannelIDs = []
            self.remove = None
            self.channelID = None
            self.message = None
            self.noxproleID = None
        else:
            self.remove = record.get('remove')
            self.message = record.get('message')
            self.channelID = record.get('channel')
            self.noxproleID = record.get('noxprole')
            self.noxpchannelIDs = record.get('noxpchannels') or []
            self.roles = record.get('roles') or []


    @property
    def channel(self):
        guild = self.bot.get_guild(self.sid)
        return guild and guild.get_channel(self.channelID)

    async def reload(self):
        record = await self.bot.db.fetchrow('SELECT * FROM config.leveling WHERE sid = $1', self.sid)
        self.remove = record['remove']
        self.message = record['message']
        self.channelID = record['channel']
        self.noxproleID = record['noxprole']
        self.roles = record['roles'] or []
        self.noxpchannelIDs = record['noxpchannels'] or []

