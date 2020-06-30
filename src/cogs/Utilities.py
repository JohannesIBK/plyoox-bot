import datetime
import random

import discord
import time
from discord.ext import commands

import main
from utils.ext import standards
from utils.ext.cmds import cmd


class Utilities(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd()
    async def someone(self, ctx):
        user = random.choice(ctx.guild.members)
        embed = discord.Embed(title='Zufälliger User :eyes:', color=standards.normal_color)
        embed.description = f"{standards.nametag_emoji} {user} ( {user.mention} )\n" \
                            f'{standards.botdev_emoji} {user.id}'
        embed.add_field(name=f'**Informationen**',
                        value=f'{standards.date_emoji} **Gejoint vor:** {(datetime.datetime.now() - user.joined_at).days} Tagen\n'
                              f'{standards.botdev_emoji} **ID:** {user.id}')
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cmd()
    async def invite(self, ctx):
        embed = discord.Embed(title=f"{standards.clyde_emoji} Invite me",
                              url=f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=268528742",
                              color=standards.normal_color)
        await ctx.send(embed=embed)

    @cmd()
    async def ping(self, ctx):
        ping = self.bot.latency * 1000
        start = time.perf_counter()
        message = await ctx.send(embed=discord.Embed(
            description=f'Pong!', color=standards.normal_color))
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(embed=discord.Embed(description='Bot: {:.2f}ms\nWebsocket: {:.2f}ms'.format(duration, ping),
                                               color=standards.normal_color))

    @cmd()
    async def bin(self, ctx, number: int):
        if number > 10000**10:
            return await ctx.send(embed=standards.getErrorEmbed('Die Zahl ist zu groß!'))
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{number} in binär ist `{str(bin(number))[2:]}`'))

    @cmd()
    async def hex(self, ctx, number: int):
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f'{number} in hexadezimal ist `{str(hex(number))[2:]}`'))


def setup(bot):
    bot.add_cog(Utilities(bot))
