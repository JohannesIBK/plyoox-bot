import datetime
import json

import discord
from discord.ext import commands

from utils.ext import standards as std, context
from utils.ext.cmds import grp

ACCEPTED_SUGGESTION_CHANNEL = 739109521452040193
DENIED_SUGGESTION_CHANNEL = 739109592541298779
WAITING_SUGGESTION_CHANNEL = 739110352913956925
IMPLEMENTED_SUGGESTION_CHANNEL = 739110320827531294
DEVELOPED_SUGGESTION_CHANNEL = 739142451771474031


class PlyooxSupport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @grp(aliases=['sg'])
    @commands.is_owner()
    async def suggestion(self, ctx: context.Context):
        pass

    @suggestion.command()
    async def accept(self, ctx: context.Context, ID: int):
        with open('utils/json/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['suggestion'] += 1
            json.dump(data, file)
            file.truncate()

        msg: discord.Message = await ctx.channel.fetch_message(ID)
        if not msg.content:
            raise commands.BadArgument('Nachricht hat keinen Content')
        acceptedChannel: discord.TextChannel = ctx.guild.get_channel(ACCEPTED_SUGGESTION_CHANNEL)
        embed = discord.Embed(color=discord.Color.green(), title='Vorschlag', timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f'#{data["suggestion"]} | {msg.author}')
        embed.description = msg.content
        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await acceptedChannel.send(embed=embed, file=attachment)
        else:
            await acceptedChannel.send(embed=embed)
        await msg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def deny(self, ctx: context.Context, ID: int):
        with open('utils/json/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['suggestion'] += 1
            json.dump(data, file)
            file.truncate()

        msg: discord.Message = await ctx.channel.fetch_message(ID)
        if not msg.content:
            raise commands.BadArgument('Nachricht hat keinen Content')
        deniedChannel: discord.TextChannel = ctx.guild.get_channel(DENIED_SUGGESTION_CHANNEL)
        embed = discord.Embed(color=discord.Color.red(), title='Vorschlag', timestamp=datetime.datetime.utcnow())
        embed.description = msg.content
        embed.set_footer(text='#' + str(data['suggestion']) )
        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await deniedChannel.send(embed=embed, file=attachment)
        else:
            await deniedChannel.send(embed=embed)
        await msg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def wait(self, ctx: context.Context, ID: int):
        with open('utils/json/simpleStorage.json', 'r+') as file:
            data = json.load(file)
            file.seek(0)
            data['suggestion'] += 1
            json.dump(data, file)
            file.truncate()

        msg: discord.Message = await ctx.channel.fetch_message(ID)
        if not msg.content:
            raise commands.BadArgument('Nachricht hat keinen Content')
        waitingChannel: discord.TextChannel = ctx.guild.get_channel(WAITING_SUGGESTION_CHANNEL)
        embed = discord.Embed(color=discord.Color.gold(), title='Vorschlag', timestamp=datetime.datetime.utcnow())
        embed.description = msg.content
        embed.set_footer(text=f'#{data["suggestion"]} | {msg.author}')
        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await waitingChannel.send(embed=embed, file=attachment)
        else:
            await waitingChannel.send(embed=embed)
        await msg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def publish(self, ctx: context.Context, ID: int):
        msg: discord.Message = await ctx.channel.fetch_message(ID)
        embed = msg.embeds[0]
        embed.color = discord.Color.blue()
        implementedChannel: discord.TextChannel = ctx.guild.get_channel(IMPLEMENTED_SUGGESTION_CHANNEL)
        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await implementedChannel.send(embed=embed, file=attachment)
        else:
            await implementedChannel.send(embed=embed)
        await msg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def publishall(self, ctx: context.Context):
        channel: discord.TextChannel = ctx.guild.get_channel(DEVELOPED_SUGGESTION_CHANNEL)
        implementedChannel: discord.TextChannel = ctx.guild.get_channel(IMPLEMENTED_SUGGESTION_CHANNEL)
        messages = await channel.history(limit=500).flatten()
    
        for msg in messages[::-1]:
            if not msg.embeds:
                continue
            embed = msg.embeds[0]
            embed.color = discord.Color.blue()  
            if msg.attachments:
                attachment = await msg.attachments[0].to_file()
                await implementedChannel.send(embed=embed, file=attachment)
            else:
                await implementedChannel.send(embed=embed)
            await msg.delete()
        await ctx.message.delete()
        
    @suggestion.command()
    async def developed(self, ctx: context.Context, ID: int):
        msg: discord.Message = await ctx.channel.fetch_message(ID)
        embed = msg.embeds[0]
        embed.color = discord.Color.dark_teal()
        developedChannel: discord.TextChannel = ctx.guild.get_channel(DEVELOPED_SUGGESTION_CHANNEL)
        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await developedChannel.send(embed=embed, file=attachment)
        else:
            await developedChannel.send(embed=embed)
        await msg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def move(self, ctx: context.Context, ID: int, toChannel: discord.TextChannel):
        msg: discord.Message = await ctx.channel.fetch_message(ID)
        embed = msg.embeds[0]

        if toChannel.id == ACCEPTED_SUGGESTION_CHANNEL:
            embed.color = discord.Color.green()
        if toChannel.id == WAITING_SUGGESTION_CHANNEL:
            embed.color = discord.Color.gold()
        if toChannel.id == DENIED_SUGGESTION_CHANNEL:
            embed.color = discord.Color.red()

        if msg.attachments:
            attachment = await msg.attachments[0].to_file()
            await toChannel.send(embed=embed, file=attachment)
        else:
            await toChannel.send(embed=embed)
        await ctx.message.delete()
        await msg.delete()

    @suggestion.command()
    async def append(self, ctx: context.Context, ID: int, suggestionID: int, channel: discord.TextChannel):
        msg: discord.Message = await channel.fetch_message(ID)
        suggestionMsg: discord.Message = await ctx.channel.fetch_message(suggestionID)
        embed = msg.embeds[0]
        embed.add_field(name=str(suggestionMsg.author), value=suggestionMsg.content)
        await msg.edit(embed=embed)
        await suggestionMsg.delete()
        await ctx.message.delete()

    @suggestion.command()
    async def dev(self, ctx: context.Context, ID: int, *, text):
        msg: discord.Message = await ctx.channel.fetch_message(ID)
        embed = msg.embeds[0]
        embed.add_field(name=f'{std.botdev_emoji} Anmerkung', value=text)
        await msg.edit(embed=embed)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(PlyooxSupport(bot))