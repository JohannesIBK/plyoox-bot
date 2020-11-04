import datetime
from typing import Union

import discord
from discord.ext import commands

import main
from utils.ext import standards as std


class Logging(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    async def createWebhook(self, guildID):
        guild = self.bot.get_guild(guildID)
        channelID = await self.bot.db.fetchval('SELECT channelid FROM config.logging WHERE sid = $1', guild.id)
        channel = guild.get_channel(channelID)
        if channel is None:
            return
        if guild.me.permissions_in(channel).manage_webhooks:
            avatar = await self.bot.user.avatar_url_as(format='webp').read()
            webhook = await channel.create_webhook(name=self.bot.user.name, avatar=avatar)
            await self.bot.db.execute('UPDATE config.logging SET token = $1, id = $2 WHERE sid = $3', webhook.token, webhook.id, guild.id)


    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        try:
            webhooks = await channel.webhooks()
        except discord.Forbidden:
            return
        if len(webhooks) == 0:
            return

        webhookID = await self.bot.db.fetchval('SELECT id FROM config.logging WHERE sid = $1', channel.guild.id)
        for webhook in webhooks:
            if webhook.id == webhookID:
                break
        else:
            await self.bot.db.execute('UPDATE config.logging SET id = NULL, token = NULL, channelid = NULL WHERE sid = $1', channel.guild.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        lang = await self.bot.lang(guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberban, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            guild.id)
        if not data or not data['logging'] or not data['memberban']:
            return

        since_joined_guild = '-----'
        if isinstance(user, discord.Member):
            since_joined_guild = (datetime.datetime.now() - user.joined_at).days

        embed = discord.Embed(color=std.normal_color, title=lang["ban.embed.title"])
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = lang["ban.embed.description"].format(u=user, d=str(since_joined_guild))
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(guild.id)


    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        lang = await self.bot.lang(guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberunban, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            guild.id)
        if not data or not data['logging'] or not data['memberunban']:
            return

        account_age = (datetime.datetime.now() - user.created_at).days

        embed = discord.Embed(color=std.normal_color, title=lang["unban.embed.title"])
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = lang["ban.embed.description"].format(u=user, d=str(account_age))
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, user: discord.Member):
        lang = await self.bot.lang(user.guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberjoin, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            user.guild.id)
        if not data or not data['logging'] or not data['memberjoin']:
            return

        account_age = (datetime.datetime.now() - user.created_at).days
        embed = discord.Embed(color=std.normal_color, title=lang["join.embed.description"])
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = lang["unban.embed.description"].format(u=user, d=str(account_age))
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(user.guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, user: discord.Member):
        lang = await self.bot.lang(user.guild.id, "logging")
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberleave, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            user.guild.id)
        if not data or not data['memberleave'] or not data['memberleave']:
            return

        since_joined_guild = (datetime.datetime.now() - user.joined_at).days
        embed = discord.Embed(color=std.normal_color, title=lang["remove.embed.title"])
        embed.set_thumbnail(url=user.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = lang["ban.embed.description"].format(u=user, d=str(since_joined_guild))
        roles = [role.mention for role in user.roles if role.name != '@everyone']
        embed.add_field(name=lang["words.roles"],
                        value=' '.join(roles) if len(roles) != 0 else '-----')
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(user.guild.id)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.guild is None:
            return

        lang = await self.bot.lang(msg.guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.msgdelete, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            msg.guild.id)
        if not data or not data['logging'] or not data['msgdelete']:
            return

        embed = discord.Embed(color=std.normal_color, title=lang["delete.embed.title"])
        embed.description = lang["delete.embed.description"].format(u=msg.author)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if not msg.content and not msg.attachments:
            return

        if msg.content:
            embed.add_field(name=lang["delete.embed.message.title"], value=std.quote(msg.content, True), inline=False)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                file = None
                if len(msg.attachments):
                    file = await msg.attachments[0].to_file(use_cached=True, spoiler=True)
                if file is not None:
                    webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url, file=file)
                else:
                    webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(msg.guild.id)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        if not payload.data or 'content' not in payload.data or 'guild_id' not in payload.data:
            return

        lang = await self.bot.lang(int(payload.data['guild_id']), "logging")
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.msgedit, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            int(payload.data['guild_id']))
        if not data or not data['logging'] or not data['msgedit']:
            return

        msgData = payload.data
        if 'author' not in msgData:
            return

        guild = self.bot.get_guild(int(payload.data["guild_id"]))
        user = guild.get_member(int(msgData['author']['id']))
        embed = discord.Embed(color=std.normal_color, title=lang["edit.embed.title"])
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)
        msg = payload.cached_message
        jump_link = f'https://discord.com/channels/{msgData["guild_id"]}/{payload.channel_id}/{payload.message_id}'
        embed.description = lang["edit.embed.description"].format(u=user, l=jump_link)

        if msg is None:
            if msgData['content']:
                embed.add_field(name=lang["edit.embed.new.title"],
                                value=std.quote(msgData['content'], True))
            else:
                return
        else:
            if msgData['content'] and msg.content is not None:
                if msgData['content'] == msg.content:
                    return
                embed.add_field(name=lang["edit.embed.old.title"],
                                value=msg.content, inline=False)
                embed.add_field(name=lang["edit.embed.new.title"],
                                value=std.quote(msgData['content'], True), inline=False)
            else:
                return

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(int(payload.data['guild_id']))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        lang = await self.bot.lang(before.guild.id, "logging")
        since_joined_guild = (datetime.datetime.now() - after.joined_at).days

        if before.display_name != after.display_name:
            data = await self.bot.db.fetchrow(
                'SELECT l.id, l.token, l.membername, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
                before.guild.id)
            if not data or not data['logging'] or not data['membername']:
                return

            embed = discord.Embed(color=std.normal_color, title=lang["update.embed.name.title"])
            embed.set_thumbnail(url=after.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.description = lang["ban.embed.description"].format(u=after, d=str(since_joined_guild))
            embed.add_field(name=lang["update.embed.name.old.title"],
                            value=f"`{before.display_name}`",
                            inline=False)
            embed.add_field(name=lang["update.embed.name.new.title"],
                            value=f"`{after.display_name}`",
                            inline=False)
            embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

            if data['id'] and data['token']:
                try:
                    webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                    webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
                except discord.NotFound:
                    await self.createWebhook(before.guild.id)

        if before.roles != after.roles:
            data = await self.bot.db.fetchrow(
                'SELECT l.id, l.token, l.memberrole, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
                before.guild.id)
            if not data or not data['logging'] or not data['memberrole']:
                return

            embed = discord.Embed(color=std.normal_color, title=lang["update.embed.role.title"])
            embed.set_thumbnail(url=after.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.description = lang["ban.embed.description"].format(u=after, d=str(since_joined_guild))

            role = list(set(before.roles) - set(after.roles)) or list(set(after.roles) - set(before.roles))

            remove = len(before.roles) > len(after.roles)
            try:
                embed.add_field(name=lang["update.embed.role.name" + ("remove" if remove else "add")],
                                value=role[0].mention)
            except:
                raise IndexError(role)

            if data['id'] and data['token']:
                try:
                    webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                    webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
                except discord.NotFound:
                    await self.createWebhook(before.guild.id)


def setup(bot):
    bot.add_cog(Logging(bot))
