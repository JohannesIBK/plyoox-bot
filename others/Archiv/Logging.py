import discord
from discord.ext import commands

from utils.ext import checks, standards


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        try:
            if payload.cached_message.author.bot:
                return
        except:
            pass

        guild_id = int(payload.data['guild_id'])

        if guild_id is None:
            return
        data = await self.bot.db.fetchrow("SELECT msglogging, msgloggingchannel FROM dcsettings WHERE sid = $1", guild_id)

        if data['msglogging']:
            channel = self.bot.get_channel(data['msgloggingchannel'])
            msg_channel = self.bot.get_channel(int(payload.data['channel_id']))

            try:
                old_msg = payload.cached_message.content
                url = payload.cached_message.jump_url
            except:
                old_msg = "No Data!"
                url = await msg_channel.fetch_message(int(payload.message_id))
                url = url.jump_url

            embed = discord.Embed(color=standards.normal_color, title="**CHAT LOGGING**", description="Message edited")
            embed.add_field(name="Author", value=self.bot.get_user(int(payload.data['author']['id'])).mention)
            embed.add_field(name="Channel", value=msg_channel.mention)
            embed.add_field(name="Neuer Content", value=f"[Jump]({url})\n{payload.data['content']}", inline=False)
            embed.add_field(name="Alter Content", value=old_msg, inline=False)

            try:
                await channel.send(embed=embed)
            except discord.HTTPException:
                embed.remove_field(2)
                embed.remove_field(2)
                embed.add_field(name="URL", value=f"[Jump]({url})")
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        guild_id = payload.guild_id

        if guild_id is None:
            return

        data = await self.bot.db.fetchrow("SELECT msglogging, msgloggingchannel FROM dcsettings WHERE sid = $1", guild_id)

        if data is None:
            return 

        if data['msglogging']:
            channel = self.bot.get_channel(data['msgloggingchannel'])
            msg_channel = self.bot.get_channel(payload.channel_id)

            if payload.cached_message is None:
                print(1)
                embed = discord.Embed(color=standards.normal_color, title="**MESSAGE DELETED**",
                                      description="No Message Data")
                embed.add_field(name="Channel", value=msg_channel.mention)
                await channel.send(embed=embed)

            else:
                msg = payload.cached_message
                embed = discord.Embed(color=standards.normal_color, title="**MESSAGE DELETED**",
                                      description=msg.content)
                embed.add_field(name="Channel", value=msg_channel.mention)
                embed.add_field(name="Author", value=msg.author)
                await channel.send(embed=embed)

    @commands.command()
    @checks.hasPerms(administrator=True)
    async def loggingchannel(self, ctx, Channel: discord.TextChannel = None):
        lang = await self.bot.lang(ctx, extras=True)

        if Channel is None:
            await self.bot.execute("UPDATE dcsettings SET msgloggingchannel = NULL WHERE sid = $1", ctx.guild.id)
            return await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                      description=lang['off']))

        perms = [perm for perm, value in ctx.author.permissions_in(ctx.channel) if value]
        if 'send_messages' not in perms:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                               description=lang['error_write_perms']))
        else:
            await ctx.db.execute("UPDATE dcsettings SET msgloggingchannel = $1 WHERE sid = $2", Channel.id, ctx.guild.id)
            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['on'].format(channel=Channel.mention)))


def setup(bot):
    bot.add_cog(Logging(bot))
