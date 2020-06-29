import time
from datetime import datetime

import pytz
from bs4 import BeautifulSoup

import discord
from discord.ext import commands, tasks

from utils.ext import checks


class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timer.start()

    # noinspection PyCallingNonCallable
    @tasks.loop(minutes=5)
    async def timer(self):
        # ignore time (1 - 9) to save quota
        not_streaming = list(range(1, 10))
        if datetime.now(tz=pytz.timezone("Europe/Vienna")).hour in not_streaming:
            return

        # get needed data
        session = self.bot.session
        channel_url = "https://www.youtube.com/channel/UCoXEsXQURGKAunhKOgGoK-Q"
        token = self.bot.yt_token
        data = await self.bot.db.fetchrow("SELECT * FROM extra.youtube WHERE sid = $1", 422077762090827786)

        # check if module is activated
        if not data["activate"]:
            return

        # check if an url is saved and sends an api request to yt to check if the stream is live
        if data["lasturl"]:
            yturl = data["lasturl"]

            url = "https://www.googleapis.com/youtube/v3/videos" \
                  "?part=liveStreamingDetails" \
                  f"&id={yturl}" \
                  f"&key={token}"

            async with session.get(url=url, headers={"Accept": "application/json"}) as resp:
                data = await resp.json()

                try:
                    # noinspection PyStatementEffect
                    data["items"][0]["liveStreamingDetails"]
                    return None
                except KeyError:
                    await self.bot.db.execute("UPDATE extra.youtube SET lasturl = $1 WHERE sid = $2", None, 422077762090827786)

        # parse yt to check if streamer is live (saves quota)
        async with session.get(url=channel_url) as resp:
            source = await resp.text()
            soup = BeautifulSoup(source, "lxml")
            is_live = soup.find_all(text="Live now")

            if is_live:
                data = str(soup.find_all(text="Live now")[0].parent)
                if '<span class="yt-badge yt-badge-live">Live now</span>' == data:
                    await self.get_stream()

    # send search request to youtube to get stream details and send it to a specific channel
    async def get_stream(self):
        session = self.bot.session
        token = self.bot.yt_token

        api_url = "https://www.googleapis.com/youtube/v3/search?" \
                  "part=snippet" \
                  "&channelId=UCoXEsXQURGKAunhKOgGoK-Q" \
                  "&eventType=live" \
                  "&type=video" \
                  f"&key={token}"

        headers = {"Accept": "application/json"}

        async with session.get(api_url, headers=headers) as resp:
            ytdata = await resp.json()
            try:
                if not ytdata["pageInfo"]["totalResults"]:
                    return

                else:
                    yt_data = ytdata["items"][0]

                    streamdata = yt_data["snippet"]
                    url_id = yt_data["id"]["videoId"]

                    data = await self.bot.db.fetchrow("SELECT * FROM extra.youtube WHERE sid = $1", 422077762090827786)

                    if not data["activate"] or data["lasturl"] == url_id:
                        return

                    url = "https://www.youtube.com/watch?v=" + url_id
                    title = streamdata["title"]
                    thumbnail = streamdata["thumbnails"]["medium"]["url"]
                    description = streamdata["description"]

                    channel = self.bot.get_channel(data["channelid"])

                    embed = discord.Embed(title=f'**{title}**',
                                          url=url,
                                          description=f'**__Link:__** {url}',
                                          color=0xfc0303
                                          )

                    embed.add_field(name="Description", value=description)
                    embed.set_image(url=thumbnail)

                    await channel.send("Snoxh ist jetzt live @everyone", embed=embed)
                    await self.bot.db.execute("UPDATE extra.youtube SET lasturl = $1 WHERE sid = $2", url_id,
                                              422077762090827786)
            except KeyError:
                return

    # if loop stops it restarts
    @timer.after_loop
    async def after_timer(self):
        self.bot.logger.info(time.strftime("YouTube Loop restarted at %d.%m.%Y um %H:%M:%S"))
        self.timer.start()

    @commands.command()
    @checks.hasPerms(administrator=True)
    async def stop(self, ctx):
        await ctx.db.execute("UPDATE extra.youtube SET activate = False")


def setup(bot):
    bot.add_cog(Youtube(bot))
