import datetime
import string
from random import random
from typing import Union

import discord

yes_emoji = "<:yes:703900321465892914>"
no_emoji = "<:no:703900335327936602>"
ola_emoji = '<:ola:703928958063738910>'
info_emoji = '<:info:703900394580869140>'
error_emoji = '<:close:704087128346329148>'
law_emoji = '<:law:704432646356467814>'
level_emoji = '<:level:704442402718482432>'
question_emoji = '\u2754'
coin_emoji = '<:coin:718169101821804564>'

# Status
online_emoji = "<:online:703932456289435659>"
offline_emoji = "<:offline:703932515349430292>"
idle_emoji = "<:idle:703932474501103706>"
dnd_emoji = "<:dnd:703932490485727232>"
streaming_emoji = '<:streaming:703900783543975956>'
bots_emoji = "<:bot:703924061004234752>"
clyde_emoji = '<:clyde:703927804563030076>'

# Badges
balance_emoji = '<:balance:703906489538183179>'
brilliance_emoji = '<:brilliance:703906573738836020>'
bavery_emoji = '<:bravery:703906586141392897>'
booster_emoji = '<:booster:703906501382766612>'
booster2_emoji = '<:booster2:703906512246145044>'
booster3_emoji = '<:booster3:703906523092484177>'
booster4_emoji = '<:booster4:703906534534414346>'

supporter_emoji = '<:supporter:703906781859938364>'
partner_emoji = '<:partner:703906812348334130>'
staff_emoji = '<:staff:703906898851790859>'
botdev_emoji = '<:botdev:703907073402077205>'
bughunter_badge = '<:bughunter:703906553325158440>'
nitro_emoji = '<:nitro:703907279795257444>'

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

# Colors
error_color = 0xff0000
normal_color = 0x7289DA
help_color = 0x38b3e8
tag_color = 0x7adeaa

avatar_url = 'https://cdn.discordapp.com/avatars/505433541916622850/ccc8ba894dd4188ecf37de0a53430f22.webp?size=1024'


# Embeds
def getEmbed(description: str) -> discord.Embed:
    """
    :param description: Message to send
    :return: discord.Embed
    """

    embed = discord.Embed(
        color=normal_color,
        description=description)

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


def getBaseModEmbed(reason: str, user: Union[discord.Member, discord.User] = None, mod: discord.Member = None):
    embed = discord.Embed(color=normal_color)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text='Plyoox Moderation', icon_url=avatar_url)

    if user is not None:
        embed.add_field(name=f'{info_emoji} **__User__**',
                        value=f'{nametag_emoji} {user}\n'
                              f'{botdev_emoji} {user.id}\n'
                              f'{mention_emoji} {user.mention}',
                        inline=False)

    if mod is not None:
        embed.add_field(name=f'{supporter_emoji} **__Moderator__**',
                        value=str(mod))

    embed.add_field(name=f'{richPresence_emoji} **__Grund__**',
                    value=reason,
                    inline=False)
    return embed


def getUserEmbed(reason: str, guildName: str, duration = 'permanent', punishType = 1):
    embed = discord.Embed(color=normal_color)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text='Plyoox Moderation', icon_url=avatar_url)

    if punishType == 0:
        embed.description = f'Du wurdest `{duration}` vom Server `{guildName}` für `{reason}` ausgeschlossen.'
    elif punishType == 1:
        embed.description = f'Du wurdest vom Server `{guildName}` für `{reason}` gekickt.'
    elif punishType == 2:
        embed.description = f'Du wurdest `{duration}` auf dem Server `{guildName}` für `{reason}` gemutet.'

    return embed


def randomString(stringLength=6):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(stringLength))
