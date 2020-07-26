import discord


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


def formatMessage(msg: str, user: discord.Member, lvl = None) -> str or None:
    guild = __Guild(user.guild)
    member = __Member(user)

    try:
        if lvl is not None:
            return msg.format(guild=guild, user=member, lvl=lvl)
        else:
            return msg.format(guild=guild, user=member)

    except:
        return None
