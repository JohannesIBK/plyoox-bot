import re

import discord
from discord.ext import commands

from utils.ext import checks, standards
from utils.ext.cmds import cmd

BRIIAAN_GUILD_ID = 665609018793787422
BRIIAAN_SUB_AUTO_ROLE = 665695035714437184
BRIIAAN_SUB_MANUELL_ROLE = 665612009240264710
BRIIAAN_SORT_ROLE = 665877391591211048


class BriiaanDE(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id != BRIIAAN_GUILD_ID:
            return

        if before.roles == after.roles:
            return

        twitch_sub_role = after.guild.get_role(BRIIAAN_SUB_AUTO_ROLE)
        sub_role = after.guild.get_role(BRIIAAN_SUB_MANUELL_ROLE)

        if sub_role in before.roles and sub_role not in after.roles or \
                twitch_sub_role in before.roles and twitch_sub_role not in after.roles:
            sort_role = after.guild.get_role(BRIIAAN_SORT_ROLE)

            if twitch_sub_role in after.roles or sub_role in after.roles:
                return
            await after.remove_roles(sort_role)

        if sub_role not in before.roles and sub_role in after.roles or \
                twitch_sub_role not in before.roles and twitch_sub_role in after.roles:
            sort_role = after.guild.get_role(BRIIAAN_SORT_ROLE)
            await after.add_roles(sort_role)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != BRIIAAN_GUILD_ID:
            return

        if member.roles is None:
            return

        twitch_sub_role = member.guild.get_role(BRIIAAN_SUB_AUTO_ROLE)
        if twitch_sub_role in member.roles:
            sort_role = member.guild.get_role(BRIIAAN_SORT_ROLE)
            await member.add_roles(sort_role)

    @cmd()
    @checks.isBriiaan()
    @checks.hasPerms(administrator=True)
    async def checkroles(self, ctx):
        sortRole = ctx.guild.get_role(BRIIAAN_SORT_ROLE)
        twitchSubRole = ctx.guild.get_role(BRIIAAN_SUB_AUTO_ROLE)
        subRole = ctx.guild.get_role(BRIIAAN_SUB_MANUELL_ROLE)

        updated = 0

        for member in sortRole.members:
            if twitchSubRole not in member.roles and subRole not in member.roles:
                await member.remove_roles(sortRole)
                updated += 1

        for member in twitchSubRole.members:
            if sortRole not in member.roles:
                await member.add_roles(sortRole)
                updated += 1

        for member in subRole.members:
            if sortRole not in member.roles:
                await member.add_roles(sortRole)
                updated += 1

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=f"Die Rolle von {updated} Usern wurde geupdated."))

    @cmd()
    @checks.isBriiaan()
    async def report(self, ctx, Spieler):
        channel = ctx.author
        await ctx.message.delete()

        def checkName():
            pattern = re.compile("^[a-z0-9-_]+$")
            return len(Spieler) in range(3, 17) and pattern.match(Spieler.lower())

        if not checkName():
            try:
                return await ctx.send(embed=standards.getErrorEmbed('Das ist kein Spielername. Bitte gib einen echten Minecraft-Namen ein.'))
            except:
                return await ctx.send(embed=standards.getErrorEmbed('Diese Funktion läuft über den DM-Chat. Bitte öffne deine DMs und versuche es erneut.'), delete_after=15)

        toChannel = ctx.guild.get_channel(666742903485235250)
        timeout = 600

        reportID = (await ctx.db.fetchval("SELECT max(report_id) FROM extra.briiaan")) + 1

        reportMsg = f'**__REPORT__** ```von: {ctx.author}```'
        reportMsg += f'\n**Report-ID:** {reportID}'
        reportMsg += f"\n\n**Reporteter Spieler**\n{Spieler}"

        reports = {"1": "Hacking", "2": "Bugusing", "3": "Name/Skin", "4": "Building", "5": "Chatverhalten"}

        def check_is_number(report_msg):
            reportMsgContent = report_msg.content.replace(".", "")
            return reportMsgContent in ["1", "2", "3", "4", "5"] and report_msg.author == ctx.author

        screens = []

        def is_valid_screen(screenLink):
            x = False

            if screenLink.author != ctx.author:
                return False

            for a in screenLink.attachments:
                screens.append(a.url)
                x = True

            if x:
                return True

            screenLinkContent = screenLink.content.replace(" ", "").split(",")

            for screen in screenLinkContent:
                if screen.startswith(("https://i.badlion.net/", "https://prnt.sc", "https://imgur.com/a/",
                                      "https://www.youtube.com/watch", "https://youtu.be/")):
                    screens.append(screen)

            if screens:
                return True

        def is_valid_video(screenLink):
            ScreenLinkContent = screenLink.content.replace(" ", "").split(",")

            if screenLink.author != ctx.author:
                return False

            for screen in ScreenLinkContent:
                if screen.startswith(("https://www.youtube.com/watch", "https://youtu.be/")):
                    screens.append(screen)

            if screens:
                return True

        def check_is_name(ig_msg):
            pattern = re.compile("^[a-z0-9-_]+$")
            return len(ig_msg.content) in range(3, 17) and pattern.match(
                ig_msg.content.lower()) and ig_msg.author == ctx.author

        def is_emoji(r_reaction, r_user):
            return str(r_reaction.emoji) in [standards.yes_emoji, standards.no_emoji] and r_user == ctx.author

        try:
            await channel.send(embed=discord.Embed(color=standards.normal_color,
                                                   title="**Das Missbrauchen dieser Funtkion wird bestraft.**",
                                                   description=f"Du reportest gerade den Spieler `{Spieler}`. Bitte folge den Schritten um den Spieler zu melden.\n\n"
                                                               "Welches Vergehen macht sich der Spieler zu schulden? Antworte mit der Nummer.\n"
                                                               "`1`. Hacking | `2`. Bugusing | `3`. Name/Skin | `4`. Building | `5`. Chatverhalten"))
        except:
            return await ctx.send(embed=standards.getErrorEmbed('Diese Funktion läuft über den DM-Chat. Bitte öffne deine DMs und versuche es erneut.'), delete_after=15)

        msgObj = await self.bot.wait_for('message', check=check_is_number, timeout=timeout)

        reason = msgObj.content.replace(".", "")
        reportMsg += f'\n\n**Art des Vergehens**\n{reports[reason]}'

        if reason in ["4", "5"]:
            await channel.send(embed=discord.Embed(color=standards.normal_color,
                                                   description="Du benötigst Beweismaterial den Spieler für das Vergehen zu melden. \n\n"
                                                               "**Bitte lade ein Bild hoch oder**\n"
                                                               "schicke einen [YouTube](https://www.youtube.com/) Video Link, oder lade ein Bild auf"
                                                               " [Imgur](https://imgur.com/upload?beta), "
                                                               " [prnt.sc](https://prnt.sc/) oder Badlion hoch. Der Bot akzeptiert nur diese Links.\n\n"
                                                               "**Trenne Links durch `,`.**"))

            await self.bot.wait_for('message', check=is_valid_screen, timeout=timeout)

            bs = "\n"
            reportMsg += f"\n\n**Beweismaterial**\n{bs.join(screens)}"

        if reason in ["1", "2"]:
            await channel.send(embed=discord.Embed(color=standards.normal_color,
                                                   description="Du benötigst Beweismaterial den Spieler für das Vergehen zu melden. "
                                                               "Antworte mit einen [YouTube](https://www.youtube.com/) Video Link. "
                                                               "Der Bot akzeptiert nur YouTube Links.\n\n"
                                                               "**Trenne Links durch `,`.**"))

            await self.bot.wait_for('message', check=is_valid_video, timeout=timeout)
            bs = "\n"
            reportMsg += f"\n\n**Beweismaterial**\n{bs.join(screens)}"

        await channel.send(embed=discord.Embed(color=standards.normal_color,
                                               description="Bitte gib deinen Minecraft-Namen an."))

        ingObj = await self.bot.wait_for('message', check=check_is_name, timeout=timeout)

        reportMsg += f'\n\n**Ersteller**\n{ingObj.content}'

        await channel.send("Dein Report:\n" + reportMsg)
        reaction_msg = await channel.send("Soll der Report abgeschickt werden?")
        await reaction_msg.add_reaction(standards.yes_emoji)
        await reaction_msg.add_reaction(standards.no_emoji)

        reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout, check=is_emoji)

        if str(reaction.emoji) == standards.yes_emoji:
            msg = await toChannel.send(reportMsg)
            await ctx.db.execute("INSERT INTO extra.briiaan (message_id, user_id, report_id) VALUES ($1, $2, $3)",
                                 msg.id, ctx.author.id, reportID)
            await channel.send("Dein Report wurde abgeschickt.")
        else:
            await channel.send("Der Report wurde abgebrochen. ")

    @cmd()
    @checks.isBriiaan()
    async def close(self, ctx, ReportID: int, Grund = None):
        message_id = await ctx.db.fetchval("SELECT message_id FROM extra.briiaan WHERE report_id = $1", ReportID)

        sendChannel = ctx.guild.get_channel(666742903485235250)
        closeChannel = ctx.guild.get_channel(666742918031081502)
        msg = await sendChannel.fetch_message(message_id)

        if msg is None:
            return await ctx.send(embed=standards.getErrorEmbed('Die Nachricht des Reports konnte nicht gefunden werden.'), delete_after=15)

        content = msg.content
        content += f'\n\n``` ```Closed by {ctx.author}'
        if Grund is not None:
            msg.content += f"\n**Grund:** {Grund}'"

        await msg.delete()
        await ctx.message.delete()
        await ctx.db.execute("DELETE FROM extra.briiaan WHERE report_id = $1", ReportID)
        await closeChannel.send(content)


def setup(bot):
    bot.add_cog(BriiaanDE(bot))
