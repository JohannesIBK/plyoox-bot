import discord
from discord.ext import commands
from discord.utils import find

from utils.ext import checks, standards


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True)
    @checks.hasPerms(administrator=True)
    async def setup(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), "setup")

    @setup.command()
    @checks.hasPerms(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def AutoMod(self, ctx):
        lang = await self.bot.lang(ctx)

        data = await ctx.db.fetchrow("SELECT modrole, logchannel FROM dcsettings WHERE sid = $1", ctx.guild.id)

        await ctx.db.execute("UPDATE dcsettings SET noinvites = $1 WHERE sid = $2", True, ctx.guild.id)
        await ctx.db.execute("UPDATE dcsettings SET banafter = $1 WHERE sid = $2", 1, ctx.guild.id)
        await ctx.db.execute("UPDATE dcsettings SET capsspam = $1 WHERE sid = $2", True, ctx.guild.id)
        await ctx.db.execute("UPDATE dcsettings SET mentionspam = $1 WHERE sid = $2", 7, ctx.guild.id)

        if data["modrole"] is None:
            mod_roles = list(filter(lambda r: "mod" in r.name.lower(), ctx.guild.roles))

            if mod_roles is None:
                await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                   description=lang['setup_modrole'].format(p=ctx.prefix)))
            else:
                for role in mod_roles:
                    perms = [perm for perm, value in role.permissions if value]

                    if any(perm in ['ban_members', 'kick_members', 'manage_messages'] for perm in perms):
                        await ctx.db.execute("UPDATE dcsettings set modrole = modrole || $1 WHERE sid = $2", {role.id}, ctx.guild.id)
                        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['setuped_modrole'].format(role=role.mention, p=ctx.prefix)))

        if data['logchannel'] is None:
            log_channel = find(lambda c: "log" in c.name.lower(), ctx.guild.channels)

            if log_channel is None:

                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }

                channel = await ctx.guild.create_text_channel("hackl-logs", position=0, reason="Logchannel needed", overwrites=overwrites)

                await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['setuped_logchannel'].format(channel=channel.mention)))
                await ctx.db.execute("UPDATE dcsettings set logchannel = $1 WHERE sid = $2", channel.id, ctx.guild.id)

            else:
                await ctx.db.execute("UPDATE dcsettings set logchannel = $1 WHERE sid = $2", log_channel.id, ctx.guild.id)
                await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['setuped_logchannel'].format(channel=log_channel.mention)))

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['setup_end']))

    @setup.command()
    async def Ticket(self, ctx):
        lang = await self.bot.lang(ctx, cogs="setup")

        data = await ctx.db.fetchrow("SELECT modrole FROM dcsettings WHERE sid = $1", ctx.guild.id)

        await ctx.db.execute("UPDATE dcsettings SET ticketsystem = True WHERE sid = $1", ctx.guild.id)

        if data["modrole"] is None:
            mod_roles = list(filter(lambda r: "mod" in r.name.lower(), ctx.guild.roles))

            if mod_roles is None:
                return await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['setup_modrole']))
            else:
                for role in mod_roles:
                    perms = [perm for perm, value in role.permissions if value]
                    if any(perm in ['ban_members', 'kick_members', 'manage_messages'] for perm in perms):
                        await ctx.db.execute("UPDATE dcsettings set modrole = modrole || $1 WHERE sid = $2", {role.id}, ctx.guild.id)
                        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['setuped_modrole'].format(role=role.mention, p=ctx.prefix)))

        data = await ctx.db.fetchrow("SELECT modrole FROM dcsettings WHERE sid = $1", ctx.guild.id)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        modroles = data['modrole']
        for roleid in modroles:
            role = ctx.guild.get_role(roleid)
            if role is None:
                await ctx.db.execute("UPDATE dcsettings SET modrole = array_remove(modrole, $1) WHERE sid = $2", roleid, ctx.guild.id)
            else:
                overwrites.update({role: discord.PermissionOverwrite(read_messages=True, send_messages=True)})

        category = await ctx.guild.create_category("TICKET-SYSTEM", overwrites=overwrites)
        ticket_channel = await category.create_text_channel("ticket-help")
        open_tickets_channel = await category.create_text_channel("open-tickets")
        await category.create_text_channel("ticket-commands")

        msg = await ticket_channel.send("Setting up...")
        ctx_new = await self.bot.get_context(msg)
        await msg.delete()
        await ctx_new.invoke(self.bot.get_command('help'), "ticket")

        await ctx.db.execute("UPDATE dcsettings SET ticketchannel = $1, ticketcategory = $2 WHERE sid = $3", open_tickets_channel.id, category.id, ctx.guild.id)


def setup(bot):
    bot.add_cog(Setup(bot))
