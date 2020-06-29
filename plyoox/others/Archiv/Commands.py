import discord
from discord.ext import commands

from utils.ext import checks, standards


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_tag(self, guild_id, name):
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE sid = $1 and LOWER(name) = $2", guild_id, name)

        if data is None:
            raise RuntimeError

        return data

    @commands.group(invoke_without_command=True, aliases=["cogs", "command"])
    async def cmd(self, ctx, *, Name):
        lang = await self.bot.lang(ctx)

        try:
            tag = await self.get_tag(ctx.guild.id, Name.lower())
            await ctx.send(embed=discord.Embed(color=standards.tag_color, title=tag['name'], description=tag['content']))
        except RuntimeError:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**", description=lang['error_not_found']))

    @cmd.command()
    @checks.tags_allowed()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def create(self, ctx, Commandname, *, Content):
        lang = await self.bot.lang(ctx)

        user_entrys = await ctx.db.fetch("SELECT name FROM tags WHERE sid = $1 AND oid = $2", ctx.guild.id, ctx.author.id)

        if len(user_entrys) >= 101:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_max_cmds']))
        data = await ctx.db.fetchrow("SELECT content FROM tags WHERE sid = $1 AND LOWER(name) = $2", ctx.guild.id, Commandname.lower())
        if data is not None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                                      description=lang['error_already_exist']))
        await ctx.db.execute("INSERT INTO tags (sid, oid, name, content, uses) VALUES ($1, $2, $3, $4, 0)", ctx.guild.id, ctx.author.id, Commandname, Content)
        await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['succeed_created']))

    @cmd.command()
    @checks.tags_allowed()
    async def delete(self, ctx, Commandname):
        lang = await self.bot.lang(ctx)

        tag = await ctx.db.fetchrow("SELECT * FROM tags WHERE sid = $1 AND LOWER(name) = $2", ctx.guild.id, Commandname.lower())
        if tag is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['error_not_found']))
        is_mod = True if 'ban_members' in "".join(perm for perm, value in ctx.author.guild_permissions if value) or ctx.message.author.id == 263347878150406144 else False

        if tag['oid'] == ctx.author.id or is_mod:
            await ctx.db.fetchrow("DELETE FROM tags WHERE sid = $1 and LOWER(name) = $2", ctx.guild.id, Commandname.lower())
            await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['succeed_deleted']))

        else:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                               description=lang['error_not_yours']))

    @cmd.command()
    @checks.tags_allowed()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def edit(self, ctx, Commandname, *, Content):
        lang = await self.bot.lang(ctx)

        tag = await ctx.db.fetchrow("SELECT * FROM tags WHERE sid = $1 AND LOWER(name) = $2", ctx.guild.id, Commandname.lower())
        if tag is None:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['error_not_found']))

        if tag['oid'] == ctx.author.id:
            await ctx.db.fetchrow("UPDATE tags SET content = $1 WHERE sid = $2 and LOWER(name) = $3", Content, ctx.guild.id, Commandname.lower())
            await ctx.send(embed=discord.Embed(color=standards.normal_color, description=lang['succeed_edited']))

        else:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                               description=lang['error_not_yours']))

    @cmd.command()
    @checks.tags_allowed()
    async def list(self, ctx, Side: int = 1):
        lang = await self.bot.lang(ctx)

        rows = list(await ctx.db.fetch("SELECT name FROM tags WHERE sid = $1", ctx.guild.id))
        embed = discord.Embed(color=standards.normal_color, title="**COMMANDS**")

        entries = int(str(Side if Side != 0 else 1) + "0")
        len_rows = len(rows)
        max_page = int(str(len_rows)[:1])

        if not rows:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['error_no_found']))

        try:
            cmd_page = rows[entries - 10:entries]
        except IndexError:
            cmd_page = rows[entries - 10:len_rows]

        if not cmd_page:
            return await ctx.send(embed=discord.Embed(color=standards.error_color, title="__**ERROR**__",
                                                      description=lang['last_page'].format(max_page=max_page)))

        if len_rows != 0:
            embed.description = "\n".join(cmd['name'] for cmd in cmd_page)
            embed.set_footer(text=lang['sides'].format(side=Side, max_page=max_page))
        await ctx.send(embed=embed)

    @cmd.command()
    @checks.hasPerms(administrator=True)
    async def clear(self, ctx):
        lang = await self.bot.lang(ctx)

        await ctx.send(embed=discord.Embed(color=standards.tag_color, title='__**WARNING**__',
                                           description=lang['clear_all']))

        def check(m):
            return m.content == 'clear all' and m.channel == ctx.message.channel

        try:
            await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(color=standards.error_color, title="**__ERROR__**",
                                               description=lang['error_time_out']))
        else:
            await ctx.db.execute("DELETE FROM tags WHERE sid = $1", ctx.guild.id)
            await ctx.send(embed=discord.Embed(color=standards.normal_color,
                                               description=lang['all_deleted']))


def setup(bot):
    bot.add_cog(Commands(bot))
