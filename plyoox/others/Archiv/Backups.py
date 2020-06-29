import asyncio
import json
import random
import string

import datetime
import discord
import time
from discord.ext import commands

from utils.ext import checks, standards


# noinspection PyArgumentList
class Backups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def create_backup(guild):
        general = {
            "name": guild.name,
            "region": guild.region[1],
            "afk_timeout": guild.afk_timeout,
            "description": guild.description,
            "mfa_level": guild.mfa_level,
            "verification_level": guild.verification_level[1],
            "explicit_content_filter": guild.explicit_content_filter[1],
            "default_notifications": guild.default_notifications[1],
            "afk_channel": guild.afk_channel.id if guild.afk_channel else None
        }

        roles = []

        for role in guild.roles:
            if role.managed:
                continue

            role_dict = {
                "oldID": role.id,
                "name": role.name,
                "hoist": role.hoist,
                "position": role.position,
                "mentionable": role.mentionable,
                "is_default": role.is_default(),
                "permissions": role.permissions.value,
                "color": role.color.value,
            }
            roles.append(role_dict)

        cats = []

        for category in guild.categories:

            overwrites_for = []
            text_channels = []
            voice_channels = []

            for role in category.changed_roles:
                if role.managed:
                    continue

                ow = category.overwrites_for(role).pair()
                perms_deny = ow[1].value
                perms_allow = ow[0].value

                role_ow = {
                    "oldID": role.id,
                    "permsAllow": perms_allow,
                    "permsDeny": perms_deny
                }
                overwrites_for.append(role_ow)

            for channel in category.text_channels:
                overwrites_for_text_channel = []

                for role in channel.changed_roles:
                    if role.managed:
                        continue

                    ow = category.overwrites_for(role).pair()
                    perms_deny = ow[1].value
                    perms_allow = ow[0].value

                    role_ow = {
                        "oldID": role.id,
                        "permsAllow": perms_allow,
                        "permsDeny": perms_deny
                    }
                    overwrites_for_text_channel.append(role_ow)

                channel_dict = {
                    "name": channel.name,
                    "topic": channel.topic,
                    "permissions_synced": channel.permissions_synced,
                    "slowmode_delay": channel.slowmode_delay,
                    "nsfw": channel.nsfw,
                    "overwrites": overwrites_for_text_channel
                }
                text_channels.append(channel_dict)

            for channel in category.voice_channels:
                overwrites_for_voice_channel = []

                for role in channel.changed_roles:
                    if role.managed:
                        continue

                    ow = channel.overwrites_for(role).pair()
                    perms_deny = ow[1].value
                    perms_allow = ow[0].value

                    role_ow = {
                        "oldID": role.id,
                        "permsAllow": perms_allow,
                        "permsDeny": perms_deny
                    }
                    overwrites_for_voice_channel.append(role_ow)

                channel_dict = {
                    "oldID": channel.id,
                    "name": channel.name,
                    "bitrate": channel.bitrate,
                    "permissions_synced": channel.permissions_synced,
                    "user_limit": channel.user_limit,
                    "overwrites": overwrites_for_voice_channel
                }
                voice_channels.append(channel_dict)

            cat_dict = {
                "name": category.name,
                "overwrites": overwrites_for,
                "channels": {
                    "text": text_channels,
                    "voice": voice_channels
                }
            }
            cats.append(cat_dict)

        no_cats_text_channels = []

        for channel in guild.text_channels:
            if channel.category is not None:
                continue

            overwrites_for_voice_channel = []

            for role in channel.changed_roles:
                if role.managed:
                    continue

                ow = channel.overwrites_for(role).pair()
                perms_deny = ow[1].value
                perms_allow = ow[0].value

                role_ow = {
                    "oldID": role.id,
                    "permsAllow": perms_allow,
                    "permsDeny": perms_deny
                }
                overwrites_for_voice_channel.append(role_ow)

            channel_dict = {
                "name": channel.name,
                "topic": channel.topic,
                "position": channel.position,
                "permissions_synced": channel.permissions_synced,
                "slowmode_delay": channel.slowmode_delay,
                "nsfw": channel.nsfw,
                "overwrites": overwrites_for_voice_channel
            }
            no_cats_text_channels.append(channel_dict)

        no_cats_voice_channels = []

        for channel in guild.voice_channels:
            if channel.category is not None:
                continue

            overwrites_for_voice_channel = []

            for role in channel.changed_roles:
                if role.managed:
                    continue

                ow = channel.overwrites_for(role).pair()
                perms_deny = ow[1].value
                perms_allow = ow[0].value

                role_ow = {
                    "oldID": role.id,
                    "permsAllow": perms_allow,
                    "permsDeny": perms_deny
                }
                overwrites_for_voice_channel.append(role_ow)

            channel_dict = {
                "oldID": channel.id,
                "name": channel.name,
                "bitrate": channel.bitrate,
                "position": channel.position,
                "permissions_synced": channel.permissions_synced,
                "user_limit": channel.user_limit,
                "overwrites": overwrites_for_voice_channel
            }

            no_cats_voice_channels.append(channel_dict)

        guild_data = {
            "general": general,
            "roles": roles,
            "categories": cats,
            "no_cats": [
                no_cats_text_channels,
                no_cats_voice_channels
            ]
        }

        return json.dumps(guild_data)

    @staticmethod
    def create_id(stringLength=10):
        """Generate a random string of fixed length """
        letters = string.ascii_letters + string.digits
        letters.replace("'", "").replace('"', "")
        return ''.join(random.choice(letters) for _ in range(stringLength))

    @commands.group()
    @checks.hasPerms(administrator=True)
    async def backup(self, ctx):
        """pass"""

    @backup.command()
    async def create(self, ctx):
        lang = await self.bot.lang(ctx)

        data_servers = await ctx.db.fetch("SELECT * FROM extra.guilds WHERE sid = $1", ctx.guild.id)

        try:
            await ctx.author.send(embed=discord.Embed(color=standards.normal_color,
                                                      description=lang["start"]))
        except:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang["error_cant_send"]))

        if data_servers is not None:
            if len(data_servers) > 3:
                msg = await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                         description=lang["error_max_backups"]))

                await msg.add_reaction(standards.yes_emoji)
                await msg.add_reaction(standards.no_emoji)

                def check(msg_reaction, msg_user):
                    return msg_user == ctx.author and str(msg_reaction.emoji) in [standards.yes_emoji, standards.no_emoji]

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(color=standards.error_color,
                                                       description=lang["error_to_long"]))
                else:
                    if str(reaction) == standards.yes_emoji:
                        id_oldest = await ctx.db.fetchval("SELECT id FROM extra.guilds WHERE time = (SELECT MIN(time) FROM guilds WHERE sid = $1)", ctx.guild.id)
                        await ctx.db.execute("DELETE FROM extra.guilds WHERE id = $1", id_oldest)

                    else:
                        return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                                  description=lang["stoped"]))

        data = self.create_backup(ctx.guild)

        id_code = self.create_id(8)

        id_code_check = await ctx.db.fetchval("DELETE FROM extra.guilds WHERE id = $1", id_code)

        base = 8

        while_t = True

        if not id_code_check:
            while while_t:
                if base == 20:
                    break

                for _ in range(10):
                    id_code = self.create_id(base)
                    id_code_check = await ctx.db.fetchval("DELETE FROM extra.guilds WHERE id = $1", id_code)
                    if id_code_check is None:
                        while_t = False

                base += 1

        await ctx.db.execute(
            "INSERT INTO extra.guilds (id, data, sid, oid, time) VALUES ($1, $2, $3, $4, $5)",
            id_code, data, ctx.guild.id, ctx.author.id, time.time())

        await ctx.author.send(embed=discord.Embed(color=standards.normal_color,
                                                  description=lang["succeed"].format(id=id_code)))

    @backup.command()
    async def delete(self, ctx, ID: str):
        lang = await self.bot.lang(ctx)

        data = await ctx.db.fetchval("SELECT id FROM extra.guilds WHERE id = $1", ID)

        if data is None:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                      description=lang["error_not_found"]))

        if ctx.guild.id == data['sid'] or ctx.author.id == data['oid']:
            msg = await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                     description=lang["delete_qustion"]))

            await msg.add_reaction(standards.yes_emoji)
            await msg.add_reaction(standards.no_emoji)

            def check(msg_reaction, msg_user):
                return msg_user == ctx.author and str(msg_reaction.emoji) in [standards.yes_emoji, standards.no_emoji]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(color=standards.error_color,
                                                   description=lang["error_to_long"]))
            else:
                if str(reaction) == standards.yes_emoji:
                    await ctx.db.execute("DELETE FROM extra.guilds WHERE id = $1", ID)
                    await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                       description=lang["succeed_delete"]))

                else:
                    return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                              description=lang["stoped_2"]))

        else:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                               description=lang["no_perms"]))

    @backup.command()
    @commands.bot_has_permissions(manage_guild=True, manage_roles=True, manage_channels=True)
    async def load(self, ctx, ID: str):
        lang = await self.bot.lang(ctx)

        role_ids = {}
        find_afk = {}

        guild_top_role = ctx.guild.roles[-1]
        if ctx.me.top_role != guild_top_role:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang["error_role_not_top"]))

        questions = {
            0: {"q": lang["q0"], "state": True},
            1: {"q": lang["q1"], "state": True},
            2: {"q": lang["q2"], "state": True},
            3: {"q": lang["q3"], "state": True},
            4: {"q": lang["q4"], "state": True}
        }

        async def ask(question, count_ask):
            msg_ask = await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                         description=question["q"]))

            await msg_ask.add_reaction(standards.yes_emoji)
            await msg_ask.add_reaction(standards.no_emoji)

            def check_ask(msg_reaction, msg_user):
                return msg_user == ctx.author and str(msg_reaction.emoji) in [standards.yes_emoji, standards.no_emoji]

            try:
                reaction_ask, user_ask = await self.bot.wait_for('reaction_add', timeout=60.0, check=check_ask)
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(color=standards.error_color,
                                                   description=lang["error_to_long"]))
            else:
                if str(reaction_ask) == standards.yes_emoji:
                    pass
                else:
                    questions[count_ask]["state"] = False

        backup = await ctx.db.fetchval("SELECT data FROM extra.guilds WHERE id = $1", ID)

        backup = json.loads(backup)

        if backup is None:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                      description=lang["error_not_found"]))

        msg = await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                 description=lang["could_delete_all"]))

        await msg.add_reaction(standards.yes_emoji)
        await msg.add_reaction(standards.no_emoji)

        def check(msg_reaction, msg_user):
            return msg_user == ctx.author and str(msg_reaction.emoji) in [standards.yes_emoji, standards.no_emoji]

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                               description=lang["error_to_long"]))
        else:
            if str(reaction) == standards.yes_emoji:
                count = 0
                for i in questions:
                    await ask(questions[i], count)
                    count += 1

                if questions[0]["state"]:
                    for role in ctx.guild.roles:
                        if role.managed or role.is_default():
                            continue
                        try:
                            await role.delete()
                        except discord.Forbidden:
                            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                                      description=lang["error_delete_channel"]))

                if questions[1]["state"]:
                    for channel in ctx.guild.channels:
                        try:
                            await channel.delete()
                        except discord.Forbidden:
                            return

                if questions[3]["state"]:
                    roles = backup["roles"]
                    if roles is not None:
                        for role in reversed(roles):
                            if role["is_default"]:
                                await ctx.guild.default_role.edit(
                                    permissions=discord.Permissions(role["permissions"])
                                )
                                role_ids.update({role["oldID"]: ctx.guild.default_role.id})
                                continue

                            try:
                                new_role = await ctx.guild.create_role(
                                    name=role["name"],
                                    colour=discord.Colour(role["color"]),
                                    hoist=role["hoist"],
                                    mentionable=role["mentionable"],
                                    permissions=discord.Permissions(role["permissions"])
                                )
                                role_ids.update({role["oldID"]: new_role.id})

                            except discord.Forbidden:
                                return

                if questions[4]["state"]:
                    for category in backup["categories"]:
                        if category["overwrites"] is not None:
                            overwrites = {}
                            if questions[4]["state"]:
                                if category["overwrites"] is not None:
                                    for role in category["overwrites"]:
                                        overwrite = discord.PermissionOverwrite().from_pair(
                                            discord.Permissions(role["permsAllow"]),
                                            discord.Permissions(role["permsDeny"])
                                        )
                                        new_role_id = role_ids[role["oldID"]]

                                        new_role = ctx.guild.get_role(new_role_id)

                                        overwrites.update({new_role: overwrite})

                            new_category = await ctx.guild.create_category(
                                name=category["name"],
                                overwrites=overwrites
                            )
                            if category["channels"] is not None:
                                if category["channels"]["text"] is not None:
                                    text_channels = category["channels"]["text"]
                                    for channel in text_channels:
                                        overwrites = {}
                                        if questions[4]["state"]:
                                            if channel["overwrites"] is not None:
                                                for role in channel["overwrites"]:
                                                    overwrite = discord.PermissionOverwrite().from_pair(
                                                        discord.Permissions(role["permsAllow"]),
                                                        discord.Permissions(role["permsDeny"])
                                                    )
                                                    new_role_id = role_ids[role["oldID"]]

                                                    new_role = ctx.guild.get_role(new_role_id)

                                                    overwrites.update({new_role: overwrite})

                                            await new_category.create_text_channel(
                                                name=channel["name"],
                                                topic=channel["topic"],
                                                slowmode_delay=channel["slowmode_delay"],
                                                permissions_synced=channel["permissions_synced"],
                                                nsfw=channel["nsfw"],
                                                overwrites=overwrites
                                            )

                                if category["channels"]["voice"] is not None:
                                    voice_channels = category["channels"]["voice"]
                                    for channel in voice_channels:
                                        overwrites = {}
                                        if questions[4]["state"]:
                                            if channel["overwrites"] is not None:
                                                for role in channel["overwrites"]:
                                                    overwrite = discord.PermissionOverwrite().from_pair(
                                                        discord.Permissions(role["permsAllow"]),
                                                        discord.Permissions(role["permsDeny"])
                                                    )

                                                    new_role_id = role_ids[role["oldID"]]

                                                    new_role = ctx.guild.get_role(new_role_id)

                                                    overwrites.update({new_role: overwrite})

                                            vc = await new_category.create_voice_channel(
                                                name=channel["name"],
                                                bitrate=channel["bitrate"],
                                                user_limit=channel["user_limit"],
                                                permissions_synced=channel["permissions_synced"],
                                                overwrites=overwrites
                                            )

                                            find_afk.update({channel["oldID"]: vc.id})

                    if backup["no_cats"]:
                        if backup["no_cats"][0]:
                            text_channels = backup["no_cats"][0]
                            for channel in text_channels:
                                overwrites = {}
                                if questions[4]["state"]:
                                    if channel["overwrites"] is not None:
                                        for role in channel["overwrites"]:
                                            overwrite = discord.PermissionOverwrite().from_pair(
                                                discord.Permissions(role["permsAllow"]),
                                                discord.Permissions(role["permsDeny"])
                                            )
                                            new_role_id = role_ids[role["oldID"]]

                                            new_role = ctx.guild.get_role(new_role_id)

                                            overwrites.update({new_role: overwrite})

                                    await ctx.guild.create_text_channel(
                                        name=channel["name"],
                                        topic=channel["topic"],
                                        position=channel["position"],
                                        slowmode_delay=channel["slowmode_delay"],
                                        permissions_synced=channel["permissions_synced"],
                                        nsfw=channel["nsfw"],
                                        overwrites=overwrites
                                    )

                        if backup["no_cats"][1]:
                            voice_channels = backup["no_cats"][1]
                            for channel in voice_channels:
                                overwrites = {}
                                if questions[4]["state"]:
                                    if channel["overwrites"] is not None:
                                        for role in channel["overwrites"]:
                                            overwrite = discord.PermissionOverwrite().from_pair(
                                                discord.Permissions(role["permsAllow"]),
                                                discord.Permissions(role["permsDeny"])
                                            )
                                            new_role_id = role_ids[role["oldID"]]

                                            new_role = ctx.guild.get_role(new_role_id)

                                            overwrites.update({new_role: overwrite})

                                    vc = await ctx.guild.create_voice_channel(
                                        name=channel["name"],
                                        bitrate=channel["bitrate"],
                                        position=channel["position"],
                                        user_limit=channel["user_limit"],
                                        permissions_synced=channel["permissions_synced"],
                                        overwrites=overwrites
                                    )

                                    find_afk.update({channel["oldID"]: vc.id})

                if questions[2]["state"]:
                    backup = backup["general"]
                    afk_timeout = backup["afk_timeout"]
                    region = discord.VoiceRegion("eu-central")
                    verification_level = discord.VerificationLevel(backup['verification_level'])
                    explicit_content_filter = discord.ContentFilter(backup["explicit_content_filter"])
                    default_notifications = discord.NotificationLevel(backup["default_notifications"])

                    if backup["afk_channel"] and questions[3]["state"]:
                        afk_channel_id = find_afk[backup["afk_channel"]]
                        afk_channel = ctx.guild.get_channel(afk_channel_id)
                    else:
                        afk_channel = None

                    await ctx.guild.edit(
                        name=backup["name"],
                        region=region,
                        afk_channel=afk_channel,
                        afk_timeout=afk_timeout,
                        verification_level=verification_level,
                        default_notifications=default_notifications,
                        explicit_content_filter=explicit_content_filter
                    )

            else:
                return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                          description=lang["stoped_2"]))

    @backup.command()
    async def list(self, ctx):
        backups = await ctx.db.fetch("SELECT id, time FROM extra.guilds WHERE sid = $1", ctx.guild.id)

        lang = await self.bot.lang(ctx)

        if backups is None:
            await ctx.send(embed=discord.Embed(color=standards.error_color,
                                               description=lang["no_backups"]))
        else:
            backup_str = "\n".join(f"ID: `{bu['id']}`, von: `{datetime.datetime.fromtimestamp(bu['time']).strftime('%d, %m, %Y')}`"
                                   for bu in backups)

            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=backup_str))


def setup(bot):
    bot.add_cog(Backups(bot))
