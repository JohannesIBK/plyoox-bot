import json
import time

from discord.ext import commands

import main
from utils.ext.cmds import grp
from utils.ext import checks, standards as std
from utils.ext.standards import *


class ParseTime():
    @classmethod
    def parse(cls, timeStr: str):
        if timeStr.endswith('d'):
            try:
                days = int(timeStr.replace('d', ''))
                if 30 < days <= 1:
                    raise TimeToLong()

                return days * 3600 * 24 + time.time()
            except:
                raise TypeError

        if timeStr.endswith('h'):
            try:
                hours = float(timeStr.replace('h', ''))
                if 48 < hours <= 0.25:
                    raise TimeToLong()

                return hours * 3600 + time.time()
            except:
                raise TypeError
        else:
            return None


class TimeToLong(Exception):
    pass


class Giveaway(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @grp(case_insensitive=True)
    @checks.isMod()
    async def giveaway(self, ctx):
        pass

    @giveaway.command()
    async def start(self, ctx, duration: str, winner: int, channel: discord.TextChannel, *, win: str):
        unixTime: float = ParseTime.parse(duration)
        data = {
            'winner': winner,
            'winType': win,
            'channel': channel.id
        }

        embed: discord.Embed = discord.Embed(color=std.normal_color,
                                             title=f'🎉 Giveaway',
                                             description=f'**Gewinn:** {win}\n'
                                                         'Reagiere mit 🎉 um dem Giveaway beizutreten.\n')

        msg: discord.Message = await channel.send(embed=embed)
        await msg.add_reaction('🎉')
        await ctx.send(embed=std.getEmbed('Das Giveaway wurde gestartet.'))
        await msg.edit(embed=discord.Embed(color=std.normal_color,
                                           title=f"🎉 Giveaway",
                                           description=f'**Gewinn:** {win} ({winner} Gewinner)\n'
                                                       'Reagiere mit 🎉 um dem Giveaway beizutreten.\n'
                                                       f'ID: {msg.id}'))
        await ctx.db.execute(
            'INSERT INTO extra.timers (sid, objid, time, type, data) VALUES ($1, $2, $3, 2, $4)',
            ctx.guild.id, msg.id, unixTime, json.dumps(data)
        )

    @giveaway.command()
    async def stop(self, ctx, ID: int):
        data = await ctx.db.execute(
            'SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        if data is None:
            return await ctx.send(embed=getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.db.execute(
            'DELETE FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        await ctx.send(embed=getEmbed('Das Giveaway wurde abgebrochen.'))
        channel: discord.TextChannel = ctx.guild.get_channel(data['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            try:
                await msg.delete()
            except:
                pass

    @giveaway.command()
    async def end(self, ctx, ID):
        data = await ctx.db.execute(
            'SELECT objid, data FROM extra.timers WHERE sid = $1 AND objid = $2',
            ctx.guild.id, ID
        )
        if data is None:
            await ctx.send(embed=getErrorEmbed('Kein Giveaway mit dieser ID gefunden.'))

        await ctx.send(embed=getEmbed('Das Giveaway wurde abgebrochen.'))
        channel: discord.TextChannel = ctx.guild.get_channel(data['channel'])
        msg = await channel.fetch_message(data['objid'])
        if msg is not None:
            self.bot.dispatch('giveaway_runout', msg, data['data'])


def setup(bot):
    bot.add_cog(Giveaway(bot))
