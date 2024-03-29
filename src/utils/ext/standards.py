import datetime

import discord

yes_emoji = "<:yes:703900321465892914>"
no_emoji = "<:no:703900335327936602>"
ola_emoji = '<:ola:703928958063738910>'
info_emoji = '<:info:703900394580869140>'
error_emoji = '<:close:820400830480908428>'
law_emoji = '<:law:704432646356467814>'
level_emoji = '<:level:704442402718482432>'
question_emoji = '\u2754'
coin_emoji = '<:coin:718169101821804564>'
upvote_emoji = '+'  # '\u2795'
downvote_emoji = '-'  # '\u2796'

# Status
online_emoji = "<:online:703932456289435659>"
offline_emoji = "<:offline:703932515349430292>"
idle_emoji = "<:idle:703932474501103706>"
dnd_emoji = "<:dnd:703932490485727232>"
streaming_emoji = '<:streaming:703900783543975956>'
bots_emoji = "<:bot:703924061004234752>"
clyde_emoji = '<:clyde:703927804563030076>'

# Badges
balance_emoji = '<:balance:820728032775372821>'
brilliance_emoji = '<:brilliance:820728032590692373>'
bravery_emoji = '<:bravery:820728032817709107>'
booster_emoji = '<:booster:703906501382766612>'
booster2_emoji = '<:booster2:703906512246145044>'
booster3_emoji = '<:booster3:703906523092484177>'
booster4_emoji = '<:booster4:703906534534414346>'

supporter_emoji = '<:supporter:703906781859938364>'
partner_emoji = '<:partner:703906812348334130>'
staff_emoji = '<:staff:703906898851790859>'
botdev_emoji = '<:botdev:703907073402077205>'
bughunter_badge = '<:bughunter:703906553325158440>'
bughunter2_badge = '<:bughunter2:747904909378060319>'
nitro_emoji = '<:nitro:703907279795257444>'
hypesquad_emoji = '<:hypesquad:314068430854684672>'

# Guild
channel_emoji = '<:channel:703906598879494257>'
lockedchannel_emoji = '<:locked_channel:703906663140294666>'
lockedVoice_emoji = '<:locked_voice:703906683918745630>'
voice_emoji = '<:voice:703906627065085973>'
verified_emoji = '<:verified:703900283192868894>'
members_emoji = '<:members:703906700889161748>'
owner_emoji = '<:owner:703906757344493649>'
invite_emoji = '<:invite:703906645113045062>'
richPresence_emoji = '<:richpresence:703907208340963378>'
mention_emoji = '<:mention:703907048760279072>'
folder_emoji = '<:folder:703900379104149534>'
nametag_emoji = '<:nametag:703936161089060895>'
globe_emoji = '\U0001F310'
stats_emoji = '\U0001F4CA'
list_emoji = '\U0001F4C4'
lock_emoji = '\U0001F512'
date_emoji = '\U0001F4C5'
inbox_emoji = '\U0001F4E5'
outbox_emoji = '\U0001F4E4'
tropy_emoji = '\U0001F3C6'
arrow = '<:arrow:762598973886169099>'

# Colors
error_color = 0xff0000
normal_color = 0x7289DA
help_color = 0x38b3e8
tag_color = 0x7adeaa
plyoox_color = 0x24c689

avatar_url = 'https://cdn.discordapp.com' \
             '/avatars/505433541916622850/ccc8ba894dd4188ecf37de0a53430f22.webp?size=1024'


def quote(string, shorten=False):
    if shorten and len(string) > 1018:
        string = string[:1015] + "..."
    return "```" + str(string) + "```"


def cut(string: str, max_len=1024):
    if len(string) > max_len:
        string = string[:1021] + "..."
    return string


# Embeds
def getEmbed(description: str = None, signed: discord.Member = None) -> discord.Embed:
    """
    :param description: Message to send
    :param signed: User who requested the command
    :return: discord.Embed
    """

    embed = discord.Embed(color=normal_color)
    if description is not None:
        embed.description = description
    if signed:
        embed.set_footer(icon_url=signed.avatar_url, text=f'Requested by {signed}')

    return embed


def getErrorEmbed(errorMessage: str) -> discord.Embed:
    """
    :param errorMessage: Message to send
    :return: discord.Embed
    """

    embed = discord.Embed(
        color=error_color,
        title=f'{error_emoji} __**ERROR**__',
        description=errorMessage)

    return embed


def dmEmbed(lang, *, reason, guildName, punishType,
            duration: datetime.timedelta = None) -> discord.Embed:
    embed = discord.Embed(color=normal_color)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=lang['log.embed.footer'], icon_url=avatar_url)
    duration = fixTimeDelta(duration)

    reason = reason or ''
    if reason:
        reason = lang['log.embed.reason'].format(r=reason)

    if punishType in ["ban", "tempban"]:
        if duration:
            embed.description = lang['log.embed.ban.temp'] \
                .format(n=guildName, r=reason, d=duration)
        else:
            embed.description = lang['log.embed.ban.perm'] \
                .format(n=guildName, r=reason)
    elif punishType == 'kick':
        embed.description = lang["log.embed.kick"].format(n=guildName, r=reason)
    elif punishType in ["tempmute", "mute"]:
        if duration:
            embed.description = lang['log.embed.mute.temp'] \
                .format(n=guildName, r=reason, d=duration)
        else:
            embed.description = lang['log.embed.mute.perm'] \
                .format(n=guildName, r=reason)

    return embed


def automodUserEmbed(lang, reason, guildName, type: str, points=None, duration: datetime.timedelta = None):
    embed = discord.Embed(color=normal_color)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=lang['log.embed.footer'], icon_url=avatar_url)

    if duration is not None:
        duration = fixTimeDelta(duration)

    if type.replace("temp", "") in ["ban", "mute"]:
        if type.startswith("temp"):
            message = lang["log.message.temp"].format(d=duration)
        else:
            message = lang["log.message.perm"]

        message = message.format(t=lang["word." + type.replace("temp", "")])
    else:
        message = lang["log.message." + type]

    if type == "log":
        message = message.format(p=points, n=guildName, r=reason)
    else:
        message = message.format(n=guildName, r=reason)

    embed.description = message
    return embed


def cmdEmbed(action, reason, lang: dict[str, str], mod=None, user=None,
             amount=None, duration: datetime.timedelta = None) -> discord.Embed:
    current_user = mod or user

    reason = reason or lang['log.noreason']
    embed = discord.Embed(color=discord.Color.orange(), title=lang["word." + action].upper())
    embed.set_footer(text="Plyoox", icon_url=avatar_url)
    embed.set_author(name=str(current_user), icon_url=current_user.avatar_url)

    if user is not None:
        embed.add_field(name=arrow + lang["word.user"], value=f"```{user} [{user.id}]```")
        embed.set_author(name=str(user), icon_url=user.avatar_url)
    if mod is not None:
        embed.add_field(name=arrow + lang["word.moderator"], value=quote(mod))
    if reason is not None:
        embed.add_field(name=arrow + lang["word.reason"], value=quote(reason))
    if duration is not None:
        embed.add_field(name=arrow + lang["word.duration"], value=quote(fixTimeDelta(duration)))
    if amount is not None:
        embed.add_field(name=arrow + lang["word.amount"], value=quote(amount))

    return embed


def automodLog(ctx, action, lang: dict[str, str], duration: datetime.timedelta,
               reason, points=None, extra_user: discord.Member = None, mod: discord.Member = None):
    user = extra_user or ctx.author
    embed = discord.Embed(
        color=plyoox_color,
        title=lang["word." + action],
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_author(name=lang["word.automod"], icon_url=user.avatar_url)
    embed.set_footer(text=f'ID: {user.id}')
    embed.description = lang[action.replace("temp", "") + ".embed.description"].format(
        u=user,
        c=ctx.channel,
        r=reason.replace(lang["word.automod"] + ": ", "")
    )

    if mod:
        embed.add_field(name=arrow + lang["word.moderator"], value=ctx.author.mention)

    if duration is not None:
        embed.add_field(name=arrow + lang["word.punishuntil"],
                        value=quote(fixTimeDelta(duration)))

    if points is not None:
        embed.add_field(name=arrow + lang["word.points"], value=quote(points))

    if not mod:
        embed.add_field(name=arrow + lang["word.message"], value=quote(ctx.message.content))

    return embed


def fixTimeDelta(time: datetime.timedelta) -> datetime.timedelta:
    if time is None:
        return
    try:
        time_str = str(time)[-2:]
        time_seconds = int(time_str)
    except (IndexError, ValueError):
        return time

    if time_seconds >= 55:
        time += datetime.timedelta(seconds=60-time_seconds)
    return time
