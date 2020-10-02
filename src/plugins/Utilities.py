import datetime
import random
import time

import discord
from discord.ext import commands

import main
from utils.ext import standards as std, context
from utils.ext.cmds import cmd


class Utilities(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd()
    async def someone(self, ctx: context.Context):
        user = random.choice(ctx.guild.members)
        embed = std.getEmbed(f'{std.nametag_emoji} {user} ( {user.mention} )\n {std.botdev_emoji} {user.id}')

        embed.title = 'Zufälliger User :eyes:'
        embed.add_field(name=f'**Informationen**',
                        value=f'{std.date_emoji} **Gejoint vor:** {(datetime.datetime.now() - user.joined_at).days} Tagen')
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @cmd()
    async def invite(self, ctx: context.Context):
        embed = discord.Embed(title=f"Hol mich {std.ola_emoji}",
                              url=f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=822471806",
                              color=std.normal_color)
        await ctx.send(embed=embed)

    @cmd()
    async def ping(self, ctx: context.Context):
        ping = self.bot.latency * 1000
        start = time.perf_counter()
        message = await ctx.embed('Pong!')
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(embed=std.getEmbed('Bot: {:.2f}ms\nWebsocket: {:.2f}ms'.format(duration, ping)))

    @cmd()
    async def bin(self, ctx: context.Context, number: int):
        if number > 10000**10:
            return await ctx.error('Die Zahl ist zu groß!')
        await ctx.embed(f'{number} in binär ist `{str(bin(number))[2:]}`')

    @cmd()
    async def hex(self, ctx: context.Context, number: int):
        await ctx.embed(f'{number} in hexadezimal ist `{str(hex(number))[2:]}`')

    @cmd()
    @commands.is_owner()
    async def infos(self, ctx: context.Context):
        embed = discord.Embed(title='**__Links__**', color=std.normal_color)
        embed.description = \
            f'**[Seite](https://plyoox.net)** `plyoox.net`\n' \
            f'**[Discord](https://go.plyoox.net/discord)** `go.plyoox.net/discord`\n' \
            f'**[Twitter](https://go.plyoox.net/twitter)** `go.plyoox.net/twitter`\n' \
            f'**[Invite](https://go.plyoox.net/invite)** `go.plyoox.net/invite`\n' \
            f'**[Voten](https://go.plyoox.net/vote)** `go.plyoox.net/vote`\n' \
            f'**[Code](https://go.plyoox.net/code)** `go.plyoox.net/code`'

        embed.add_field(name='**#support**',
                        value='[*(click)*](https://canary.discordapp.com/channels/694790265382109224/694790266275496004/) '
                              'Wenn du Fragen hast oder dir unsicher bist, wie etwas funktioniert kannst du hier gerne fragen.',
                        inline=False)
        embed.add_field(name='**#bugs**',
                        value='[*(click)*](https://canary.discordapp.com/channels/694790265382109224/700996133685559336/) '
                              'Hast du einen Bug gefunden? Melde ihn hier und er wird so schnell wie möglich gefixt.',
                        inline=False)
        embed.add_field(name='#einrichen',
                        value='[*(click)*](https://canary.discordapp.com/channels/694790265382109224/739108334069612594/) '
                              'Wenn du einen Vorschlag hast oder dir beim Bot noch etwas fehlt, kannst du die Funktion hier vorschlagen. '
                              'Schau aber vorher nach ob es noch nciht vorgeschlagen wurde.')

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
