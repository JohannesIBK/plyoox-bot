import datetime
import json

import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from utils.ext import standards


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def stats(self, player, modi, lang):
        if modi.lower() == "survivalgames 1.14":
            modi_id = "survivalgames114"
        else:
            modi_id = modi.lower()

        games = []
        lst = []
        gomme_stats = {}

        url = f'https://www.gommehd.net/player/index?playerName={player}'

        session = self.bot.session
        async with session.get(url) as resp:
            source = await resp.text()

        soup = BeautifulSoup(source, "lxml")
        if soup.title.text == "Statistiken":
            return lang['player_not_found']

        statsall = soup.find('div', class_='row profile-gametype-stats')
        for i in soup.find_all('div', class_='col-md-4 stat-table'):
            games.append(i.span.text.lower())

        if modi.lower() not in games:
            return lang['modi_not_found']

        statsGame = statsall.find(id=modi_id)
        statsOfGame = statsGame.find_all('li')

        for i in statsOfGame:
            lst.extend(list(filter(None, i.text.split("\n"))))

        for i in range(len(lst)):
            if i % 2:
                continue
            gomme_stats.update({lst[i + 1].replace(" ", ""): lst[i]})
        return gomme_stats

    @commands.command()
    async def gomme(self, ctx, Spieler: str, *, Modi: str):
        lang = await self.bot.lang(ctx)

        stats = await self.stats(Spieler, Modi, lang)
        link = f'https://www.gommehd.net/player/index?playerName={Spieler.lower()}'

        if not isinstance(stats, dict):
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, description=stats))

        else:
            embed = discord.Embed(color=standards.normal_color, title=f"Stats from `{Spieler.upper()}`", description=f'Modus: {Modi.upper()}', url=link)
            for i in stats:
                embed.add_field(name=i, value=stats[i], inline=False)
            if "Deaths" in stats and "Kills" in stats:
                if int(stats["Deaths"]) == 0:
                    kd = int(stats["Kills"])
                elif int(stats["Kills"]) == 0:
                    kd = 0
                else:
                    kd = int(stats["Kills"]) / int(stats["Deaths"])
                embed.add_field(name="KD", value=str(round(kd, 2)))
            await ctx.send(embed=embed)

    @commands.command()
    async def namehistory(self, ctx, Name):
        lang = await self.bot.lang(ctx)

        session = self.bot.session

        url_history_str = "https://api.mojang.com/user/profiles/{}/names"
        url = "https://api.mojang.com/profiles/minecraft"
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        payload = json.dumps(Name)

        response = await session.post(url, data=payload, headers=headers)
        data = await response.json()

        if not data:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['error']))
        uuid = data[0]['id']

        url_history = url_history_str.format(uuid)

        async with session.get(url_history) as resp:
            data_json = await resp.json()
        embed = discord.Embed(color=standards.normal_color, title=f"Namehistory from {Name}", description=f"UUID: `{uuid}`")
        for data in data_json:
            try:
                time_int = int(str(data['changedToAt'])[:-3])
                changedToAt = datetime.datetime.fromtimestamp(time_int).strftime("%d %B %Y")
            except:
                changedToAt = lang['org_name']
            embed.add_field(name=f"`{data['name']}`", value=changedToAt)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Minecraft(bot))
