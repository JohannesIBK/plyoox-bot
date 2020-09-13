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
        guild: discord.Guild = self.bot.get_guild(guildID)
        channelID = await self.bot.db.fetchval('SELECT channelid FROM config.logging WHERE sid = $1', guild.id)
        channel: discord.TextChannel = guild.get_channel(channelID)
        if channel is None:
            return
        if guild.me.permissions_in(channel).manage_webhooks:
            avatar = await self.bot.user.avatar_url_as(format='webp').read()
            webhook: discord.Webhook = await channel.create_webhook(name=self.bot.user.name, avatar=avatar)
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
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberban, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            guild.id)
        if not data or not data['logging'] or not data['memberban']:
            return

        embed = discord.Embed(color=std.normal_color, title = 'LOGGING [BAN]')
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = f'{user} wurde gebannt.'
        embed.add_field(name=f'{std.info_emoji} **__User__**',
                        value=f'{std.nametag_emoji} {user}\n'
                              f'{std.botdev_emoji} {user.id}\n',
                        inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(guild.id)


    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberunban, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            guild.id)
        if not data or not data['logging'] or not data['memberunban']:
            return

        embed = discord.Embed(color=std.normal_color, title = 'LOGGING [UNBAN]')
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = f'{user} wurde entbannt.'
        embed.add_field(name=f'{std.info_emoji} **__User__**',
                        value=f'{std.nametag_emoji} {user}\n'
                              f'{std.botdev_emoji} {user.id}\n',
                        inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, user: discord.Member):
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberjoin, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            user.guild.id)
        if not data or not data['logging'] or not data['memberjoin']:
            return

        days_dc = (datetime.datetime.now() - user.created_at).days
        embed = discord.Embed(color=std.normal_color, title='LOGGING [JOIN]')
        embed.set_thumbnail(url=user.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = f'{std.inbox_emoji} {user} ist dem Discord gejoint.'
        embed.add_field(name=f'{std.info_emoji} **__User__**',
                        value=f'{std.nametag_emoji} {user}\n'
                              f'{std.botdev_emoji} {user.id}\n'
                              f'{std.mention_emoji} {user.mention}',
                        inline=False)
        embed.add_field(name=f'{std.date_emoji} Account-Alter', value=str(days_dc), inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(user.guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, user: discord.Member):
        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.memberleave, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            user.guild.id)
        if not data or not data['memberleave'] or not data['memberleave']:
            return

        since_joined_guild = (datetime.datetime.now() - user.joined_at).days
        embed = discord.Embed(color=std.normal_color, title = 'LOGGING [LEAVE]')
        embed.set_thumbnail(url=user.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        embed.description = f'{std.outbox_emoji} {user} hat den Discord verlassen.'
        embed.add_field(name=f'{std.info_emoji} **__User__**',
                        value=f'{std.nametag_emoji} {user}\n'
                              f'{std.botdev_emoji} {user.id}\n',
                        inline=False)
        embed.add_field(name=f'{std.date_emoji} Tage auf dem Server', value=str(since_joined_guild), inline=False)
        roles = [role.mention for role in user.roles if role.name != '@everyone']
        embed.add_field(name=f'{std.mention_emoji} **__Rollen__**',
                        value=' '.join(roles) if len(roles) != 0 else '-----')
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(user.guild.id)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.guild is None:
            return

        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.msgdelete, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            msg.guild.id)
        if not data or not data['logging'] or not data['msgdelete']:
            return

        embed = discord.Embed(color=std.normal_color, title = 'LOGGING [MESSAGE DELETE]')
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)
        embed.add_field(name=f'{std.info_emoji} **__Author__**',
                        value=f'{std.nametag_emoji} {msg.author}\n'
                              f'{std.botdev_emoji} {msg.author.id}\n'
                              f'{std.mention_emoji} {msg.author.mention}',
                        inline=False)

        if not msg.content and not msg.attachments:
            return

        if msg.content:
            embed.add_field(name=f'{std.richPresence_emoji} **__Nachricht__**', value=msg.content, inline=False)

        if msg.attachments:
            files = [f'[Hier klicken]({attachment.url})' for attachment in msg.attachments]
            embed.add_field(name=f'{std.folder_emoji} **__Anhänge__**', value='\n'.join(files), inline=False)

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(msg.guild.id)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if not payload.data or 'content' not in payload.data or 'guild_id' not in payload.data:
            return

        data = await self.bot.db.fetchrow(
            'SELECT l.id, l.token, l.msgedit, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
            int(payload.data['guild_id']))
        if not data or not data['logging'] or not data['msgedit']:
            return

        msgData = payload.data
        if 'author' not in msgData:
            return
        user = msgData['author']
        embed = discord.Embed(color=std.normal_color, title='LOGGING [MESSAGE EDIT]')
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)
        msg: discord.Message = payload.cached_message
        embed.description = f'[Springe zur Nachricht](https://discord.com/channels/{msgData["guild_id"]}/{payload.channel_id}/{payload.message_id})'
        embed.add_field(name=f'{std.info_emoji} **__User__**',
                        value=f'{std.nametag_emoji} {user["username"]}#{user["discriminator"]}\n'
                              f'{std.botdev_emoji} {user["id"]}\n'
                              f'{std.mention_emoji} <@{user["id"]}>',
                        inline=False)

        if msg is None:
            if not msgData['content']:
                return
            embed.add_field(name=f'{std.richPresence_emoji} **__Neue Nachricht__**',
                            value=msgData['content'])
        else:
            if msgData['content'] and msg.content is not None:
                if msgData['content'] == msg.content:
                    return
                embed.add_field(name=f'{std.richPresence_emoji} **__Neue Nachricht__**',
                                value=msgData['content'], inline=False)
                embed.add_field(name=f'{std.richPresence_emoji} **__Alte Nachricht__**',
                                value=msg.content, inline=False)
            else:
                return

        if data['id'] and data['token']:
            try:
                webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                # noinspection PyAsyncCall
                webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
            except discord.NotFound:
                await self.createWebhook(int(payload.data['guild_id']))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.display_name != after.display_name:
            data = await self.bot.db.fetchrow(
                'SELECT l.id, l.token, l.membername, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
                before.guild.id)
            if not data or not data['logging'] or not data['membername']:
                return

            embed = discord.Embed(color=std.normal_color, title='MEMBER [NAME UPDATE]')
            embed.set_thumbnail(url=after.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.add_field(name=f'{std.info_emoji} **__User__**',
                            value=f'{std.nametag_emoji} {before}\n'
                                  f'{std.botdev_emoji} {before.id}\n'
                                  f'{std.mention_emoji} {before.mention}',
                            inline=False)
            embed.add_field(name=f'{std.nametag_emoji} **__Alter Name__**',
                            value=before.display_name,
                            inline=False)
            embed.add_field(name=f'{std.nametag_emoji} **__Neuer Name__**',
                            value=after.display_name,
                            inline=False)
            embed.set_footer(text='Plyoox Logging', icon_url=self.bot.user.avatar_url)

            if data['id'] and data['token']:
                try:
                    webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                    # noinspection PyAsyncCall
                    webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
                except discord.NotFound:
                    await self.createWebhook(before.guild.id)

        if before.roles != after.roles:
            data = await self.bot.db.fetchrow(
                'SELECT l.id, l.token, l.memberrole, m.logging FROM config.logging l INNER JOIN config.modules m ON l.sid = m.sid WHERE l.sid = $1',
                before.guild.id)
            if not data or not data['logging'] or not data['memberrole']:
                return

            embed = discord.Embed(color=std.normal_color, title='MEMBER [ROLE UPDATE]')
            embed.set_thumbnail(url=after.avatar_url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.add_field(name=f'{std.info_emoji} **__User__**',
                            value=f'{std.nametag_emoji} {before}\n'
                                  f'{std.botdev_emoji} {before.id}\n'
                                  f'{std.mention_emoji} {before.mention}',
                            inline=False)
            role = list(set(before.roles) - set(after.roles)) or list(set(after.roles) - set(before.roles))

            remove = len(before.roles) > len(after.roles)
            try:
                embed.add_field(name=f'{std.downvote_emoji if remove else std.upvote_emoji} **__Rolle {"REMOVE" if remove else "ADD"}__**',
                                value=role[0].mention)
            except:
                raise IndexError(role)

            if data['id'] and data['token']:
                try:
                    webhook = discord.Webhook.partial(data['id'], data['token'], adapter=discord.RequestsWebhookAdapter())
                    # noinspection PyAsyncCall
                    webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
                except discord.NotFound:
                    await self.createWebhook(before.guild.id)


def setup(bot):
    bot.add_cog(Logging(bot))
