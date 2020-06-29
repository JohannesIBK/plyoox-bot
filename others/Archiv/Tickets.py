import random
import string

import discord
from discord.ext import commands

from utils.ext import checks, standards


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @activate.command()
    async def ticket(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET ticketsystem = $1 WHERE sid = $2", True, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang['ticket']))

    @deactivate.command(name="ticket")
    async def _ticket(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.fetch("UPDATE dcsettings SET ticketsystem = $1 WHERE sid = $2", False, ctx.guild.id)

        await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                           description=lang[ctx.command.name].format(p=ctx.prefix)))

    @commands.group(aliases=["t"])
    @checks.isActive('ticketsystem')
    async def ticket(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.bot.get_command('help'), ctx.command.name)

    @ticket.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def new(self, ctx, *, Content):
        lang = await self.bot.lang(ctx)

        data = await ctx.db.fetchrow("SELECT ticketchannel, ticketcategory, modrole FROM dcsettings WHERE sid = $1", ctx.guild.id)
        if data is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_no_setup'].format(p=ctx.prefix)))
        tid = None

        def ticketid_gen():
            letters = string.ascii_letters + string.digits

            t_id = ''.join(random.choice(letters) for _ in range(random.randint(3, 7)))
            return t_id

        i = 0
        while i < 20:
            unprooft_tid = ticketid_gen()
            key = await ctx.db.fetchrow("SELECT tid FROM support WHERE tid = $1", unprooft_tid)
            if key is not None:
                i += 1
                continue
            else:
                tid = unprooft_tid
                break

        if tid is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_no_ticketid']))

        channel = ctx.guild.get_channel(data['ticketchannel'])
        if channel is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_no_ticketchannel'], inline=False))

        if data['modrole']:
            mod_roles = " ".join(f'<@&{role}>' for role in data['modrole'])
        else:
            mod_roles = None

        embed = discord.Embed(color=standards.normal_color)
        embed.title = lang['ticket_title'].format(tid=tid)
        embed.add_field(name=f'{ctx.author}', value=f'{ctx.author.mention} [{ctx.author.id}]')
        embed.add_field(name=lang['your_question'], value=Content, inline=False)
        await channel.send(mod_roles, embed=embed)

        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['ticket_succeed']), delete_after=30)

        await ctx.db.execute("INSERT INTO support (tid, sid, uid, content) VALUES ($1, $2, $3, $4)", tid, ctx.guild.id, ctx.author.id, Content)

    @ticket.command()
    @checks.isMod()
    @commands.bot_has_permissions(manage_channels=True)
    async def open(self, ctx, ID: str):
        lang = await self.bot.lang(ctx)

        data = await ctx.db.fetchrow("SELECT * FROM support WHERE tid = $1 AND sid = $2", ID, ctx.guild.id)
        settings = await ctx.db.fetchrow("SELECT ticketchannel, ticketcategory, modrole FROM dcsettings WHERE sid = $1", ctx.guild.id)

        if data is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_ticketid_not_found']))

        user = ctx.guild.get_member(data['uid'])

        if user is None:
            await ctx.db.execute("DELETE FROM support WHERE sid = $1 and uid = $2", ctx.guild.id, data['uid'])
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="**__ERROR__**",
                                                      description=lang['error_user_not_found']))
        if user.status == discord.Status.offline:
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="**__ERROR__**",
                                                      description=lang['error_user_offline'].format(p=ctx.prefix)))

        category = ctx.guild.get_channel(settings['ticketchannel']).category
        if category.id != settings['ticketcategory'] or category is None:
            await self.bot.execute("UPDATE dcsettings SET ticketcategory = NULL, ticketchannel = NULL WHERE sid = $10", ctx.guild.id)
            return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="**__ERROR__**",
                                                      description=lang['error_setup_changed']))

        overwrites = {
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        modroles = settings['modrole']
        for roleid in modroles:
            role = ctx.guild.get_role(roleid)
            if role is None:
                await ctx.db.execute("UPDATE dcsettings SET modrole = array_remove(modrole, $1) WHERE sid = $2", roleid, ctx.guild.id)
            else:
                overwrites.update({role: discord.PermissionOverwrite(read_messages=True, send_messages=True)})

        channel = await category.create_text_channel("Support", overwrites=overwrites)
        await ctx.db.execute("UPDATE support SET channelid = $1 WHERE tid = $2", channel.id, ID)

    @ticket.command()
    @checks.isMod()
    async def answer(self, ctx, ID: str, Answer):
        lang = await self.bot.lang(ctx)

        data = await ctx.db.fetchrow("SELECT * FROM support WHERE tid = $1 AND sid = $2", ID, ctx.guild.id)

        if data is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_ticketid_not_found']))
        user = ctx.guild.get_member(data['uid'])

        if user is None:
            if user is None:
                await ctx.db.execute("DELETE FROM support WHERE sid = $1 and uid = $2", ctx.guild.id, data['uid'])
                return await ctx.send(embed=discord.Embed(color=standards.normal_color, title="**__ERROR__**",
                                                          description=lang['error_user_not_found']))

        try:
            embed = discord.Embed(color=standards.normal_color, title="**SUPPORT ANSWER**",
                                  description=lang['embed_title'].format(id=ID, user=ctx.author.mention))
            embed.add_field(name=lang['your_question'], value=data['content'])
            embed.add_field(name=lang['answer'], value=Answer)
            await user.send(embed=embed)
            await ctx.db.execute("DELETE FROM support WHERE tid = $1", ID)
            await ctx.send(embed=discord.Embed(color=standards.normal_color))

        except:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                               description=lang['error_cannot_send_dm']))

    @ticket.command()
    @checks.isMod()
    @commands.bot_has_permissions(manage_channels=True)
    async def close(self, ctx, ID: str = None):
        lang = await self.bot.lang(ctx)

        open_ticket_channel = await ctx.db.fetchval("SELECT ticketchannel FROM dcsettings WHERE sid = $1", ctx.guild.id)

        async def get_msg(ticket_id):
            cnl = ctx.guild.get_channel(open_ticket_channel)
            async for msg in cnl.history(limit=300):
                try:
                    if ticket_id in msg.embeds[0].title:
                        await msg.delete()
                except:
                    pass

        if ID is None:
            channelid = ctx.channel.id
            ticket = await ctx.db.fetchval("SELECT tid FROM support WHERE channelid = $1", channelid)
            if ticket is None:
                await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                   description=lang['error_not_for_support']))
            else:
                await ctx.db.execute("DELETE FROM support WHERE tid = $1", ticket)
                await ctx.channel.delete()
                await get_msg(ticket)

        else:
            data = await ctx.db.fetchrow("SELECT * FROM support WHERE tid = $1", ID)
            if data is None:
                await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                   description=lang['error_ticketid_not_found']))
            else:
                await ctx.db.execute("DELETE FROM support WHERE tid = $1 AND sid = $2", ID, ctx.guild.id)
                await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                                   description=lang['ticket_closed']))
                await get_msg(ID)

    @ticket.command()
    @checks.isMod()
    async def list(self, ctx, Side: int = 1):
        lang = await self.bot.lang(ctx)

        tickets = list(await ctx.db.fetch("SELECT * FROM support WHERE sid = $1", ctx.guild.id))
        embed = discord.Embed(color=standards.normal_color, title="**TICKETS**")

        entries = int(str(Side if Side != 0 else 1) + "0")
        len_tickets = len(tickets)
        max_page = int(str(len_tickets)[:1]) + 1

        if not tickets:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['error_no_open_tickets']))

        try:
            tickets_page = tickets[entries - 10:entries]
        except IndexError:
            tickets_page = tickets[entries - 10:len_tickets]

        if not tickets_page:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=f"{lang['last_page']}: {max_page}."))

        if len_tickets != 0:
            for ticket in tickets_page:
                user = ctx.guild.get_member(ticket['uid'])
                if user is None:
                    return await ctx.db.execute("DELETE FROM support WHERE sid = $1 and uid = $2", ctx.guild.id, ticket['user'])
                embed.add_field(name=f'User: {user} [TicketID: {ticket["tid"]}]', value=ticket['content'], inline=False)
            embed.set_footer(text=f"{lang['word_side']}: {Side}/{max_page}")
        await ctx.send(embed=embed)

    @ticket.command()
    @checks.hasPerms(administartor=True)
    async def clear(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.db.execute("DELETE FROM support WHERE sid = $1", ctx.guild.id)
        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['all_cleared']))


def setup(bot):
    bot.add_cog(Tickets(bot))
