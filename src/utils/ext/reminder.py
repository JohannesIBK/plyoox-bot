import json


class Timer:
    __slots__ = ("object_id", "sid", "data", "time", "type", "id")

    @classmethod
    async def create_timer(cls, sid: int, *, time: int, object_id: int, type: str, data: dict = None):
        self = cls()
        self.sid = sid
        self.object_id = object_id
        self.time = time
        self.type = type
        self.data = data

        return self

    @classmethod
    def load_timer(cls, record):
        self = cls()
        self.id = record["id"]
        self.object_id = record["objid"]
        self.time = record["time"]
        self.type = record["type"]
        self.data = json.loads(record["data"])
        self.sid = record["sid"]

        return self

    async def delete_timer(self, con):
        await con.execute("DELETE FROM extra.timers WHERE id = $1", self.id)