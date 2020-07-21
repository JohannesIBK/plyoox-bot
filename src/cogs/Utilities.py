import datetime
import random
import time

import discord
from discord.ext import commands

import main
from utils.ext import standards as std
from utils.ext.cmds import cmd


class Utilities(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd()
    async def someone(self, ctx):
        user = random.choice(ctx.guild.members)
        embed = std.getEmbed(f'{std.nametag_emoji} {user} ( {user.mention} )\n {std.botdev_emoji} {user.id}')

        embed.title = 'Zufälliger User :eyes:'
        embed.add_field(name=f'**Informationen**',
                        value=f'{std.date_emoji} **Gejoint vor:** {(datetime.datetime.now() - user.joined_at).days} Tagen')
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cmd()
    async def invite(self, ctx):
        embed = discord.Embed(title=f"Hol mich {std.ola_emoji}",
                              url=f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=268528742",
                              color=std.normal_color)
        await ctx.send(embed=embed)

    @cmd()
    async def ping(self, ctx):
        ping = self.bot.latency * 1000
        start = time.perf_counter()
        message = await ctx.send(embed=std.getEmbed('Pong!'))
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(embed=std.getEmbed('Bot: {:.2f}ms\nWebsocket: {:.2f}ms'.format(duration, ping)))

    @cmd()
    async def bin(self, ctx, number: int):
        if number > 10000**10:
            return await ctx.send(embed=std.getErrorEmbed('Die Zahl ist zu groß!'))
        await ctx.send(embed=std.getEmbed('{number} in binär ist `{str(bin(number))[2:]}`'))

    @cmd()
    async def hex(self, ctx, number: int):
        await ctx.send(embed=std.getEmbed(f'{number} in hexadezimal ist `{str(hex(number))[2:]}`'))


def setup(bot):
    bot.add_cog(Utilities(bot))
