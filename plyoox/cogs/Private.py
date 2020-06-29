import discord
from discord.ext import commands

import main
from utils.ext import checks, standards
from utils.ext.cmds import cmd

CHANNEL_ID = 423143055885860864
CATEGORY_ID = 422077762090827789
GUILD_ID = 422077762090827786

CUSTOM_CHANNEL_ID = None
CUSTOM_ROLE_ID = None


class Private(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.channelIDs = [CHANNEL_ID]
        self.state = True


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.state:
            return

        if member.guild.id != GUILD_ID:
            return

        if after.channel is not None:
            if after.channel.id not in self.channelIDs:
                return

            if len(after.channel.members) >= 1:
                for channel in self.channelIDs:
                    channel = member.guild.get_channel(channel)
                    if channel and len(channel.members) == 0:
                        return

                category = self.bot.get_channel(CATEGORY_ID)
                channel = await category.create_voice_channel(f'Talk (x2👤) #{len(self.channelIDs) + 1}', user_limit=2, reason='Channel Creation | Add')
                self.channelIDs.append(channel.id)
                return

        if before.channel is not None:
            if before.channel.id == CHANNEL_ID:
                for channel in self.channelIDs:
                    channelObj = member.guild.get_channel(channel)
                    if channelObj and not len(channelObj.members) and channel != CHANNEL_ID:
                        await channelObj.delete()
                        self.channelIDs.remove(channel)
                return

            if before.channel.id not in self.channelIDs:
                return

            if len(before.channel.members) == 0:
                await before.channel.delete(reason='Channel Creation | Remove')
                self.channelIDs.remove(before.channel.id)


    @cmd(showHelp=False)
    @checks.hasPerms(manage_messages=True)
    async def channelCreator(self, ctx):
        if ctx.guild.id != GUILD_ID:
            return

        self.state = not self.state
        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=f'Status des Channel-Creators wurde auf `{self.state}` gesetzt.'))

    @cmd(showHelp=False)
    @checks.hasPerms(administrator=True)
    async def addCustomRole(self, ctx, Channel: discord.VoiceChannel, Rolle: discord.Role):
        members = Channel.members
        added = 0

        for member in members:
            added += 1
            await member.add_roles(Rolle)

        await ctx.send(f'Die Rolle wurde {added} Usern gegeben.')


def setup(bot):
    bot.add_cog(Private(bot))
