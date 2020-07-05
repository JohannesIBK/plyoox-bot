import codecs
import json

import main

import discord
from discord.ext import commands

from utils.ext import standards
from utils.ext.cmds import cmd


class Help(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.helpText = json.load(codecs.open(r'others/help_de.json', encoding='utf-8'))

    @cmd()
    async def help(self, ctx, command = None):
        arg = ''
        if command is not None:
            arg: str = command.lower()

        modules = dict((key.lower(), [key, value]) for key, value in self.bot.cogs.items()
                       if key.lower() not in ['loader', 'errors', 'owner', 'help', 'private', 'events'])

        if arg == '':
            embed: discord.Embed = discord.Embed(title=f'{standards.question_emoji} Command Hilfe',
                                                 description=f'[Dashboard](https://plyoox.net/) | [Support](https://discordapp.com/invite/5qPPvQe)',
                                                 color=standards.help_color)
            embed.set_footer(icon_url=ctx.me.avatar_url)

            for module in modules:
                cog = modules[module]

                if ctx.guild.id != 665609018793787422 and module == "briiaande":
                    continue

                cmds = [module_cmd for module_cmd in cog[1].get_commands() if module_cmd.showHelp]

                embed.add_field(name=cog[0], value=f'> {", ".join(f"`{module_cmd}`" for module_cmd in cmds)}', inline=False)
                embed.set_footer(text=f"{ctx.prefix}help <Modul>",
                                 icon_url=ctx.me.avatar_url)
            await ctx.send(embed=embed)

        elif arg in self.bot.get_all_commands:
            try:
                cmdObj: commands.Command = self.bot.get_all_commands[arg]
            except KeyError:
                return await ctx.send(embed=standards.getErrorEmbed('Für diesen Command ist keine Hilfe verfügbar.'))
            cmdHelpRaw: list = self.helpText[cmdObj.name.lower()].copy()
            if cmdObj.aliases:
                cmdHelpRaw.insert(1, f'\n**__Alias:__** {", ".join(f"`{alias}`" for alias in cmdObj.aliases)}')
            cmdHelp: str = '\n'.join(cmdHelpRaw)
            await ctx.send(embed=discord.Embed(color=standards.help_color,
                                               title=f'**__Command Hilfe für {cmdObj.name}__**',
                                               description=cmdHelp.format(p=ctx.prefix)))

        elif arg.lower() in modules:
            cogHelp: commands.Cog = modules[arg.lower()][1]
            command: commands.Command
            embed: discord.Embed = discord.Embed(color=standards.help_color,
                                                 title=f'{standards.question_emoji} Modul-Hilfe')

            for command in cogHelp.get_commands():
                cmdHelpRaw: list = self.helpText[command.name.lower()].copy()
                cmdHelp: str = cmdHelpRaw[0]
                embed.add_field(name=f'**{command.name}** {command.signature}', value=cmdHelp.format(p=ctx.prefix), inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.send(embed=standards.getErrorEmbed('Dieser Command exsitiert nicht.'))


def setup(bot):
    bot.add_cog(Help(bot))
