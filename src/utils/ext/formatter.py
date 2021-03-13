import discord


class NoRoleReached(Exception):
    pass


class __Member:
    def __init__(self, member: discord.Member):
        self.name = member.name
        self.display_name = member.display_name
        self.discriminator = member.discriminator
        self.mention = member.mention
        self.id = member.id
        self.avatar = member.avatar_url

    def __str__(self):
        return f'{self.name}#{self.discriminator}'


class __Guild:
    def __init__(self, guild: discord.Guild):
        self.member_count = guild.member_count
        self.name = guild.name
        self.premium_subscribers = guild.premium_subscription_count
        self.id = guild.id
        self.icon = guild.icon_url

    def __str__(self):
        return self.name


class __Level:
    def __init__(self, lvl, role: discord.Role = None):
        self.role = role
        self.lvl = str(lvl)

    def __str__(self):
        return self.lvl

    @property
    def role(self):
        if self._role:
            return self._role.mention
        raise NoRoleReached

    @role.setter
    def role(self, value):
        self._role = value

    @property
    def rolelvl(self):
        if self._role:
            return self._role.mention
        return self.lvl


def formatMessage(msg: str, user: discord.Member, lvl=None, role: discord.Role = None) -> str or None:
    guild = __Guild(user.guild)
    member = __Member(user)
    level = __Level(lvl, role)

    try:
        if lvl is not None:
            return msg.format(guild=guild, user=member, lvl=level)
        else:
            return msg.format(guild=guild, user=member)
    except (KeyError, NoRoleReached):
        return None
