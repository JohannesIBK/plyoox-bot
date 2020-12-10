import datetime
from os import name
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
    
    # pylint: disable=unsubscriptable-object
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        lang = await self.bot.lang(guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberban, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            guild.id)
        if not data or not data['logging'] or not data['memberban']:
            return

        since_joined_guild = '-'
        if isinstance(user, discord.Member):
            since_joined_guild = (datetime.datetime.now() - user.joined_at).days

        embed = discord.Embed(color=discord.Color.red())
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_author(name=lang["ban.embed.title"], icon_url=user.avatar_url)
        embed.description = lang["ban.embed.description"].format(u=user, d=since_joined_guild)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f'ID: {user.id}')

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

        embed = discord.Embed(color=discord.Color.green())
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_author(name=lang["unban.embed.title"], icon_url=user.avatar_url)
        embed.description = lang["unban.embed.description"].format(u=user, d=account_age)
        embed.set_footer(text=f'ID: {user.id}')

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

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=lang["join.embed.title"], icon_url=user.avatar_url)
        embed.description = lang["join.embed.description"].format(u=user, d=account_age)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f'ID {user.id}')

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
        embed = discord.Embed(color=discord.Color.red())
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_author(name=lang["remove.embed.title"], icon_url=user.avatar_url)
        embed.description = lang["remove.embed.description"].format(u=user, d=since_joined_guild)
        roles = [role.mention for role in user.roles if role.name != '@everyone']
        embed.add_field(
            name=std.arrow + lang["words.roles"],
            value=' '.join(roles) if len(roles) != 0 else '-----'
        )
        embed.set_footer(text=f'ID: {user.id}')

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(user.guild.id)

    @commands.Cog.listener()
    async def on_message_delete(self, cached_message: discord.Message):
        if cached_message.guild is None:
            return

        lang = await self.bot.lang(cached_message.guild.id, "logging", utils=True)
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.msgdelete, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            cached_message.guild.id)

        if not data or not data['logging'] or not data['msgdelete']:
            return

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=lang["delete.embed.title"], icon_url=cached_message.author.avatar_url)
        embed.description = lang["delete.embed.description"].format(c=cached_message.channel.mention, u=cached_message.author)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f'ID: {cached_message.author.id}')

        if not cached_message.content and not cached_message.attachments:
            return

        if cached_message.content:
            embed.add_field(
                name=std.arrow + lang["delete.embed.message.title"], 
                value=std.cut(cached_message.content), 
                inline=False
            )

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(cached_message.guild.id)

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

        payload_message = payload.data
        if 'author' not in payload_message:
            return

        guild = self.bot.get_guild(int(payload.data["guild_id"]))
        user = guild.get_member(int(payload_message['author']['id']))
        cached_message = payload.cached_message

        embed = discord.Embed(color=discord.Color.orange())
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_author(name=lang["edit.embed.title"], icon_url=user.avatar_url)
        embed.set_footer(text=f"ID: {payload_message['author']['id']}", icon_url=self.bot.user.avatar_url)

        jump_link = f'https://discord.com/channels/{guild.id}/{payload.channel_id}/{payload.message_id}'
        embed.description = lang["edit.embed.description"].format(
            l=jump_link, 
            c=guild.get_channel(int(payload.data["channel_id"])).mention,
            u=user    
        )

        if cached_message is None:
            if payload_message['content']:
                embed.add_field(
                    name=std.arrow + lang["edit.embed.new.title"],
                    value=std.cut(payload_message['content'])
                )
            else:
                return
        else:
            if payload_message['content'] and cached_message.content is not None:
                if payload_message['content'] == cached_message.content:
                    return
                embed.add_field(
                    name=std.arrow + lang["edit.embed.old.title"],
                    value=std.cut(cached_message.content),
                    inline=False
                )
                embed.add_field(
                    name=std.arrow + lang["edit.embed.new.title"],
                    value=std.cut(payload_message['content']),
                    inline=False
                )
            else:
                return

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                webhook.execute(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(guild.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        lang = await self.bot.lang(before.guild.id, "logging")

        if before.display_name != after.display_name:
            data = await self.bot.db.fetchrow(
                'SELECT l.id, l.token, l.membername, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
                before.guild.id)
            if not data or not data['logging'] or not data['membername']:
                return

            embed = discord.Embed(color=discord.Color.orange())
            embed.set_author(name=lang["name.embed.title"], icon_url=after.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.description = lang["name.embed.description"].format(b=before, a=after)
            embed.set_footer(text=f'ID: {after.id}')

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

            embed = discord.Embed()
            embed.set_author(name=lang["role.embed.title"], icon_url=after.avatar_url)
            embed.set_footer(text=f"ID: {after.id}")
            embed.timestamp = datetime.datetime.utcnow()

            role = list(set(before.roles) - set(after.roles)) or list(set(after.roles) - set(before.roles))

            try:
                if len(before.roles) > len(after.roles):
                    embed.color = discord.Color.dark_blue()
                    embed.description = lang["role.embed.remove"].format(r=role[0], u=after)
                else:
                    embed.color = discord.Color.blue()
                    embed.description = lang["role.embed.add"].format(r=role[0], u=after)
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
