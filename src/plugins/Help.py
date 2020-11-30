import json

import discord
from discord.ext import commands

import main
from utils.ext import standards, context
from utils.ext.cmds import cmd


class Help(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot
        self.languages = {}
        self.load_langs()

    def load_langs(self):
        languages_list = ["de", "en"]

        for lang in languages_list:
            with open(f"utils/languages/{lang}/help_{lang}.json", encoding="utf-8") as f:
                data = json.load(f)
                self.languages.update({lang: data})

    @cmd(aliases=["commands"])
    async def help(self, ctx: context.Context, command = None):
        lang = await ctx.lang(module="help")
        config = await ctx.cache.get(ctx.guild.id)

        arg = ''
        if command is not None:
            arg = command.lower()

        modules = dict((key.lower(), [key, value]) for key, value in self.bot.cogs.items()
                       if key.lower() not in ['loader', 'errors', 'owner', 'help', 'private', 'events', 'logging', 'plyooxsupport', 'botlists', "commands"])

        if arg == '':
            prefix = '@Plyoox#1355'
            if config.prefix is not None:
                prefix = config.prefix

            embed = discord.Embed(title=lang["help.embed.title"],
                                  description=f'[{lang["help.word.dashboard"]}](https://plyoox.net/) | '
                                              f'[{lang["help.word.support"]}](https://discordapp.com/invite/5qPPvQe) | '
                                              f'[{lang["help.word.invite"]}](https://go.plyoox.net/invite) '
                                              f'\n{lang["word.lang.prefix"]}: `{prefix[-1]}`',
                                  color=standards.help_color)
            embed.set_footer(icon_url=ctx.me.avatar_url)
            disabledModules = []

            for module in modules:
                cog = modules[module]

                if hasattr(config.modules, module):
                    if config.modules is not None and config.modules.__getattribute__(module) == False:
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
                cmdHelpRaw = self.languages[config.lang][cmdObj.name.lower()].copy()
            except KeyError:
                return await ctx.error(lang["help.error.nohelp"])

            if cmdObj.aliases:
                cmdHelpRaw.insert(1, f'\n**__{lang["help.word.alias"]}:__** {", ".join(f"`{alias}`" for alias in cmdObj.aliases)}')
            cmdHelp = '\n'.join(cmdHelpRaw)

            embed = discord.Embed(
                color=standards.help_color,
                title=lang["help.embed.command.title"].format(c=cmdObj.name),
                description=cmdHelp.format(p=ctx.prefix))
            embed.set_footer(text=lang["help.embed.footer.args"])

            await ctx.send(embed=embed)

        elif arg.lower() in modules:
            cogHelp: commands.Cog = modules[arg.lower()][1]
            command: commands.Command
            embed = discord.Embed(color=standards.help_color, title=lang["help.embed.modul.title"])

            for command in cogHelp.get_commands():
                cmdHelpRaw = self.languages[config.lang][command.name.lower()].copy()
                cmdHelp = cmdHelpRaw[0]
                embed.add_field(name=f'**{command.name}** {command.signature}', value=cmdHelp.format(p=ctx.prefix), inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.error(lang["help.error.notacommand"])


def setup(bot):
    bot.add_cog(Help(bot))
