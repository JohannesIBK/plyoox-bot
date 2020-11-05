import codecs
import json

import discord
from discord.ext import commands

import main
from utils.ext import standards, context
from utils.ext.cmds import cmd


class Help(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.helpText = json.load(codecs.open(r'utils/json/help_de.json', encoding='utf-8'))

    @cmd()
    async def help(self, ctx: context.Context, command = None):
        lang = await ctx.lang()
        arg = ''
        if command is not None:
            arg = command.lower()

        modules = dict((key.lower(), [key, value]) for key, value in self.bot.cogs.items()
                       if key.lower() not in ['loader', 'errors', 'owner', 'help', 'private', 'events', 'logging', 'plyooxsupport', 'botlists'])


        if arg == '':
            prefix = '@Plyoox#1355'

            data = await ctx.db.fetchrow(
                'SELECT c.prefix, m.* FROM config.guild c INNER JOIN config.modules m ON c.sid = m.sid WHERE c.sid = $1',
                ctx.guild.id)
            if data['prefix'] is not None:
                prefix = data['prefix']

            embed = discord.Embed(title=lang["help.embed.title"],
                                                 description=f'[{lang["help.word.dashboard"]}](https://plyoox.net/) | [{lang["help.word.support"]}](https://discordapp.com/invite/5qPPvQe) | [{lang["help.word.invite"]}](https://go.plyoox.net/invite) \n{lang["word.lang.prefix"]}: `{prefix}`',
                                                 color=standards.help_color)
            embed.set_footer(icon_url=ctx.me.avatar_url)
            disabledModules = []

            for module in modules:
                cog = modules[module]
                if data.get(module) is not None and data.get(module) == False:
                    disabledModules.append(cog[0])
                    continue


                if ctx.guild.id != 665609018793787422 and module == "briiaande":
                    continue

                cmds = [module_cmd for module_cmd in cog[1].get_commands() if module_cmd.showHelp]

                embed.add_field(name=cog[0], value=f'> {", ".join(f"`{module_cmd}`" for module_cmd in cmds)}', inline=False)
                embed.set_footer(text=f"{ctx.prefix}help <{lang['help.word.module']}>",
                                 icon_url=ctx.me.avatar_url)

            if disabledModules:
                embed.add_field(name=lang["help.embed.deactivated.title"],
                                value=' '.join(f'`{module}`' for module in disabledModules))

            await ctx.send(embed=embed)

        elif arg in self.bot.get_all_commands:
            try:
                cmdObj: commands.Command = self.bot.get_all_commands[arg]
                cmdHelpRaw = self.helpText[cmdObj.name.lower()].copy()
            except KeyError:
                return await ctx.error(lang["help.error.nohelp"])
            if cmdObj.aliases:
                cmdHelpRaw.insert(1, f'\n**__{lang["help.word.alias"]}:__** {", ".join(f"`{alias}`" for alias in cmdObj.aliases)}')
            cmdHelp = '\n'.join(cmdHelpRaw)
            await ctx.send(embed=discord.Embed(color=standards.help_color,
                                               title=lang["help.embed.command.title"].format(c=cmdObj.name),
                                               description=cmdHelp.format(p=ctx.prefix)))

        elif arg.lower() in modules:
            cogHelp: commands.Cog = modules[arg.lower()][1]
            command: commands.Command
            embed = discord.Embed(color=standards.help_color, title=lang["help.embed.modul.title"])

            for command in cogHelp.get_commands():
                cmdHelpRaw = self.helpText[command.name.lower()].copy()
                cmdHelp = cmdHelpRaw[0]
                embed.add_field(name=f'**{command.name}** {command.signature}', value=cmdHelp.format(p=ctx.prefix), inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.error(lang["help.error.notacommand"])


def setup(bot):
    bot.add_cog(Help(bot))
