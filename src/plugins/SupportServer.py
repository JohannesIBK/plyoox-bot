import datetime

import discord
from discord.ext import commands

import main
from utils.ext.cmds import cmd
from utils.ext.context import Context


ACCEPTED_CHANNEL = 813065438673371176

TRELLO_API = "https://api.trello.com/1"


with open("utils/keys/trello.env", "r") as tokenFile:
    tokens = tokenFile.readlines()
    key = tokens[0].replace("\n", "")
    token = tokens[1].replace("\n", "")


class PlyooxSupport(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    @cmd()
    @commands.has_role(443095214240956417)
    async def confirmbug(self, ctx: Context, message: discord.Message):
        data = {
            "key": key,
            "token": token,
            "idList": "6031915acbc6047b7610d1f6",
            "name": f"Bug #{message.id}",
            "desc": message.content + f"\n\nBy **{message.author}**",
        }

        async with self.bot.session.post(TRELLO_API + "/cards", data=data) as res:
            if res.status == 200:
                res_data = await res.json()
                card_id = res_data["id"]
                card_url = res_data["url"]

                if message.attachments:
                    counter = 1
                    for attachment in message.attachments:
                        attachment_data = {
                            "key"   : key,
                            "token" : token,
                            "id"    : card_id,
                            "name"  : f"Attachment #{counter}",
                            "file"  : await attachment.read()
                        }

                        async with self.bot.session.post(
                                TRELLO_API + f"/cards/{card_id}/attachments",
                                data=attachment_data):
                            counter += 1

                embed = discord.Embed(
                    title="Bug",
                    colour=discord.Color.dark_green())
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_author(name=message.author.name, icon_url=message.author.avatar)
                embed.add_field(name="Bug", value=message.content, inline=False)
                embed.add_field(name="Trello (Status)", value=card_url, inline=False)
                embed.set_footer(text=f"ID: {message.id}")
                await ctx.guild.get_channel(ACCEPTED_CHANNEL).send(embed=embed)
            else:
                await ctx.error(f"Ein Fehler ist aufgetreten: API Response Code: {res.status}")

    @cmd()
    @commands.has_role(443095214240956417)
    async def confirmsuggestion(self, ctx: Context, message: discord.Message):
        data = {
            "key"   : key,
            "token" : token,
            "idList": "60319141c6c12b3507564e40",
            "name"  : f"Vorschlag #{message.id}",
            "desc"  : message.content + f"\n\nBy **{message.author}**",
        }

        async with self.bot.session.post(TRELLO_API + "/cards", data=data) as res:
            if res.status == 200:
                res_data = await res.json()
                card_id = res_data["id"]
                card_url = res_data["url"]

                if message.attachments:
                    counter = 1
                    for attachment in message.attachments:
                        attachment_data = {
                            "key"  : key,
                            "token": token,
                            "id"   : card_id,
                            "name" : f"Attachment #{counter}",
                            "file" : await attachment.read()
                        }

                        async with self.bot.session.post(
                                TRELLO_API + f"/cards/{card_id}/attachments",
                                data=attachment_data):
                            counter += 1

                embed = discord.Embed(
                    title="Vorschlag",
                    colour=discord.Color.dark_green())
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_author(name=message.author.name, icon_url=message.author.avatar)
                embed.add_field(name="Vorschlag", value=message.content, inline=False)
                embed.add_field(name="Anhänge",
                                value=str(len(message.attachments) or "Keine Anhänge"),
                                inline=False)
                embed.add_field(name="Trello (Status)", value=card_url, inline=False)
                embed.set_footer(text=f"ID: {message.id}")
                await ctx.guild.get_channel(ACCEPTED_CHANNEL).send(embed=embed)
                await message.delete(delay=10)
                await ctx.message.delete(delay=10)
            else:
                await ctx.error(f"Ein Fehler ist aufgetreten.\nAPI Response Code: {res.status}")


def setup(bot):
    bot.add_cog(PlyooxSupport(bot))
