import discord
from discord.ext import commands

import main
from utils.ext import checks, standards
from utils.ext.cmds import grp


class Commands(commands.Cog):
    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    async def command_list(self, ctx):
        userID = self.bot.user.id
        msg = ctx.message.content.split(" ")

        if msg[0] in [f'<@!{userID}> ', f'<@{userID}> ']:
            try:
                command = ctx.message.content.split(" ")[1]
            except IndexError:
                return
        else:
            command: str = msg[0].replace(ctx.prefix, '')

        custom_command = await ctx.db.fetchrow("SELECT * FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, command)
        if custom_command is None:
            return

        content = custom_command['content']
        await ctx.send(content, allowed_mentions=discord.AllowedMentions(everyone=True, roles=True, users=True))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if msg.guild is None:
            return

        if not isinstance(msg.author, discord.Member):
            return

        ctx = await self.bot.get_context(msg)
        if ctx.command:
            return

        prefixes = [f'<@!{self.bot.user.id}> ', f'<@{self.bot.user.id}> ', await self.bot.get(msg.guild.id, 'prefix')]

        if msg.content.startswith(tuple(prefixes)):
            await self.command_list(ctx)

    @grp(name="command")
    @checks.isAdmin()
    async def command_cmd(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), "command")

    @command_cmd.command()
    async def add(self, ctx, name, *, content):
        name = name.lower()

        all_commands = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)

        if all_commands is not None:
            if len(all_commands) > 50:
                return await ctx.send(embed=standards.getErrorEmbed('Der Server darf maximal 50 Commands besitzen.'))

        if self.bot.get_command(name) is not None:
            return await ctx.send(embed=standards.getErrorEmbed('Dieser Command darf nicht erstellt werden.'))

        cmd = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is not None:
            return await ctx.send(embed=standards.getErrorEmbed('Dieser Command existiert bereits.'))

        await ctx.db.execute("INSERT INTO extra.commands (sid, name, content) VALUES ($1, $2, $3)", ctx.guild.id, name, content)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Command wurde erfolgreich hinzugefügt.'))

    @command_cmd.command()
    async def edit(self, ctx, name, *, content):
        name = name.lower()

        cmd = await ctx.db.fetchval("SELECT name, content FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Command wurde nicht gefunden.'))

        await ctx.db.execute("UPDATE extra.commands SET content = $1 WHERE sid = $2 AND name = $3", content, ctx.guild.id, name)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Command wurde erfolgreich bearbeitet.'))

    @command_cmd.command(aliases=['delete', 'del'])
    async def remove(self, ctx, name):
        name = name.lower()

        all_commands = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)

        if not all_commands:
            return await ctx.send(embed=standards.getErrorEmbed('Der Server besitzt keine Commands.'))

        cmd = await ctx.db.fetchval("SELECT name FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)

        if cmd is None:
            return await ctx.send(embed=standards.getErrorEmbed('Der Command wurde nicht gefunden.'))

        await ctx.db.execute("DELETE FROM extra.commands WHERE sid = $1 AND name = $2", ctx.guild.id, name)
        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description='Der Command wurde erfolgreich entfernt.'))

    @command_cmd.command()
    async def list(self, ctx):
        all_commands = await ctx.db.fetch("SELECT name FROM extra.commands WHERE sid = $1", ctx.guild.id)

        if not all_commands:
            return await ctx.send(embed=standards.getErrorEmbed('Der Server besitzt keine Commands.'))

        embed = discord.Embed(color=standards.normal_color,
                              description=", ".join(f'{cmd["name"]}' for cmd in all_commands))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
