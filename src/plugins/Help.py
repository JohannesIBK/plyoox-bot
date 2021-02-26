import json
from typing import Mapping
from typing import Optional

import discord
from discord.ext import commands

from utils.ext import context
from utils.ext import standards as std


languages = {}


def load_langs():
    languages_list = ["de", "en"]

    for lang in languages_list:
        with open(f"utils/languages/{lang}/help_{lang}.json", encoding="utf-8") as f:
            data = json.load(f)
            languages.update({lang: data})


load_langs()


class HelpCommand(commands.HelpCommand):
    def get_context(self) -> context.Context:
        return self.context

    def get_command_signature(self, command: commands.Command, prefix=True):
        prefix = self.clean_prefix if prefix else ""
        signature = "" or command.signature
        if signature:
            signature = " " + signature.replace("<", "< **`").replace(">", "`** >")\
                .replace("[", "[ `").replace("]", "` ]")

        return prefix + command.qualified_name + signature

    async def subcommand_not_found(self, command: commands.Command, string: str):
        await self.send_command_help(command)

    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.get_context()
        lang = await ctx.lang(module="help")
        config = await ctx.cache.get(ctx.guild.id)

        embed = discord.Embed(color=std.help_color,
                              description=lang["embed.description.cmdhelp"].format(
                                  p=self.clean_prefix))

        for command in cog.get_commands():
            if command.hidden:
                continue
            embed.add_field(name=command.qualified_name + " " + command.signature,
                            value=languages[config.lang][command.qualified_name.lower()][0],
                            inline=False)

        embed.set_footer(text=lang["embed.footer.args"])

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        ctx = self.get_context()
        lang = await ctx.lang(module="help")
        config = await ctx.cache.get(ctx.guild.id)

        if command.hidden:
            return await self.send_error_message(lang["error.command.nohelp"])

        embed = discord.Embed(title=self.get_command_signature(command, False),
                              color=std.help_color)
        embed.set_footer(text=lang["embed.footer.args"])

        if len(command.qualified_name.split()) > 1:
            try:
                raw_description = \
                    languages[config.lang][command.qualified_name.lower().split()[0]][1][
                        command.qualified_name.lower().split()[1]]
                if isinstance(raw_description, list):
                    raw_description = "\n".join(raw_description)
                embed.description = raw_description
            except KeyError:
                return await self.command_not_found(command.qualified_name)
        else:
            raw_description = languages[config.lang][command.qualified_name.lower().split()[0]]
            if isinstance(raw_description, list):
                raw_description = "\n".join(raw_description)
            embed.description = raw_description

        if command.qualified_name.split(" ")[0] in ["giveaway", "tempban", "tempmute", "reminder"]:
            embed.description = embed.description.format(t=lang["word.times"])

        if command.aliases:
            embed.description += "\n\n**" + lang["word.aliases"] + ":** " + ", ".join(
                f"`{alias}`" for alias in command.aliases)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        ctx = self.get_context()
        lang = await ctx.lang(module="help")
        config = await ctx.cache.get(ctx.guild.id)

        if group.hidden:
            return await self.send_error_message(lang["error.command.nohelp"])

        embed = discord.Embed(title=self.get_command_signature(group, False), color=std.help_color)
        embed.set_footer(text=lang["embed.footer.args"])
        embed.description = languages[config.lang][group.qualified_name.lower()][0]

        if group.aliases:
            embed.description += "\n\n**" + lang["word.aliases"] + ":** " + ", ".join(
                f"`{alias}`" for alias in group.aliases)

        subcommands = []
        for command in group.commands:
            subcommands.append(self.get_command_signature(command, False))

        embed.add_field(name=lang["embed.group.subcommands"], value="\n".join(subcommands))

        await self.get_destination().send(embed=embed)

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], list[commands.Command]]):
        ctx = self.get_context()
        lang = await ctx.lang(module="help")

        embed = discord.Embed(color=std.help_color)
        embed.description = lang["embed.description.help"].format(p=self.clean_prefix)
        embed.set_footer(text=lang["embed.footer.args"])

        for cog in mapping:
            cmds = []
            for command in mapping[cog]:
                if not command.hidden:
                    cmds.append("`" + command.qualified_name + "`")

            if len(cmds):
                embed.add_field(name=cog.qualified_name, value=", ".join(cmds), inline=False)

        await self.get_destination().send(embed=embed)

    async def command_not_found(self, command_name: str):
        lang = await self.get_context().lang(module="help")
        return lang["error.command.notfound"].format(c=command_name)

    async def send_error_message(self, error: str):
        destination = self.get_destination()
        embed = std.getErrorEmbed(error)
        await destination.send(embed=embed)


class NewHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(NewHelp(bot))
