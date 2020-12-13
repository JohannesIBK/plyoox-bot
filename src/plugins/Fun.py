import argparse
import json
import random

import discord
from discord.ext import commands

import main
from utils.ext import checks, standards as std, context
from utils.ext.cmds import cmd


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class Fun(commands.Cog):
    with open('utils/json_files/gif_links.json_files', encoding='utf-8') as gifs:
        gifData = json.load(gifs)

    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    # --------------------------------commands--------------------------------

    @cmd()
    @checks.isActive('fun')
    async def color(self, ctx: context.Context):
        lang = await ctx.lang()

        rgbs = []
        for _ in range(0, 3, 1):
            rgbs.append(random.choice(range(256)))
        color = discord.Colour.from_rgb(rgbs[0], rgbs[1], rgbs[2])
        color_hex = "#%02x%02x%02x" % (rgbs[0], rgbs[1], rgbs[2])
        await ctx.send(embed=discord.Embed(color=color,
                                           description=lang["color.message"].format(r=rgbs, h=color_hex)))

    @cmd()
    @checks.isActive('fun')
    async def minesweeper(self, ctx: context.Context):
        columns = 10
        rows = 10
        bombs = 10

        grid: list = [[0 for _ in range(columns)] for _ in range(rows)]

        loop_count = 0
        while loop_count < bombs:
            x = random.randint(0, columns - 1)
            y = random.randint(0, rows - 1)

            if grid[y][x] == 0:
                grid[y][x] = 'B'
                loop_count = loop_count + 1

            if grid[y][x] == 'B':
                pass

        pos_x = 0
        pos_y = 0
        while pos_x * pos_y < columns * rows and pos_y < rows:

            adj_sum = 0
            for (adj_y, adj_x) in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:

                try:
                    if grid[adj_y + pos_y][adj_x + pos_x] == 'B' and adj_y + pos_y > -1 and adj_x + pos_x > -1:
                        adj_sum = adj_sum + 1
                except Exception:
                    pass

            if grid[pos_y][pos_x] != 'B':
                grid[pos_y][pos_x] = adj_sum

            if pos_x == columns - 1:
                pos_x = 0
                pos_y = pos_y + 1
            else:
                pos_x = pos_x + 1

        string_builder = []
        for reihen in grid:
            string_builder.append(''.join(map(str, reihen)))

        string_builder = '\n'.join(string_builder)
        string_builder = string_builder.replace('0', '||:zero:||')
        string_builder = string_builder.replace('1', '||:one:||')
        string_builder = string_builder.replace('2', '||:two:||')
        string_builder = string_builder.replace('3', '||:three:||')
        string_builder = string_builder.replace('4', '||:four:||')
        string_builder = string_builder.replace('5', '||:five:||')
        string_builder = string_builder.replace('6', '||:six:||')
        string_builder = string_builder.replace('7', '||:seven:||')
        string_builder = string_builder.replace('8', '||:eight:||')
        final = string_builder.replace('B', '||:bomb:||')

        await ctx.send(content=f'\U0000FEFF\n{final}')

    @cmd()
    @checks.isActive('fun')
    async def dice(self, ctx: context.Context):
        zahl = random.choice([":one:", ":two:", ":three:", ":four:", ":five:", ":six:"])
        await ctx.send(zahl)

    @cmd()
    @checks.isActive('fun')
    async def ship(self, ctx: context.Context, user1: discord.Member, user2: discord.Member = None):
        lang = await ctx.lang()

        if user2 is None:
            user2 = ctx.message.author

        if user1 == user2:
            return await ctx.error(lang["multi.error.sameuser"])

        score = random.randint(0, 100)
        filled_progbar = round(score / 100 * 10)
        counter = f"{'█' * filled_progbar}{' ' * (10 - filled_progbar)}"

        embed = discord.Embed(color=0xfc03df)
        embed.title = f"{user1.display_name} ❤ {user2.display_name}"
        embed.description = f"`{counter}` **{score}%** "

        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def thisorthat(self, ctx: context.Context, *, questions: str):
        lang = await ctx.lang()

        if 'discord.gg' in questions.lower() or 'discord.com/invite' in questions.lower():
            return
        if questions.count('|') == 0:
            return await ctx.error(lang["thisorthat.error.needmultiple"])

        questions_list = questions.split('|')
        choosen = random.choice(questions_list)
        await ctx.embed(lang["thisorthat.message"].format(c=choosen.strip()), allowed_mentions=discord.AllowedMentions.none(), signed=True)

    @cmd()
    @checks.isActive('fun')
    async def coinflip(self, ctx: context.Context):
        flip = ['<:coin:718169101821804564>', '<:supporter:703906781859938364>']
        emoji = random.choice(flip)
        await ctx.send(emoji)

    @cmd(aliases=['slots'])
    @checks.isActive('fun')
    @commands.cooldown(rate=3, per=1, type=commands.BucketType.member)
    async def slot(self, ctx: context.Context):
        lang = await ctx.lang()
        emojis = ("🍎", '🍉', '🍇', '🍓', '🍒')

        selected = ''
        for _ in range(3):
            selected += random.choice(emojis)

        if len(set(selected)) == 1:
            await ctx.embed(lang["slot.message.prize"].format(s=''.join(selected)), signed=True)
        else:
            await ctx.embed(lang["slot.message.lose"].format(s=''.join(selected)), signed=True)

    @cmd()
    @checks.isActive('fun')
    async def reverse(self, ctx: context.Context, *, text: str):
        reversed_text = text[::-1]
        if 'discord.gg' in reversed_text.lower() or 'discord.com/invite' in reversed_text.lower():
            return

        await ctx.embed(reversed_text, signed=True)

    @cmd()
    @checks.isActive('fun')
    async def caseing(self, ctx: context.Context, *, text: str):
        if 'discord.gg' in text.lower() or 'discord.com/invite' in text.lower():
            return
        new_text = []
        last_upper = False

        for word in text.split(" "):
            t = ""
            for i in range(len(word)):
                char = word[i]
                if not last_upper:
                    t += char.upper()
                    last_upper = True
                else:
                    t += char.lower()
                    last_upper = False
            new_text.append(t)

        await ctx.embed(f'```{" ".join(new_text)}```', signed=True)

    @cmd()
    @checks.isActive('fun')
    async def pat(self, ctx: context.Context, user: discord.Member):
        lang = await ctx.lang()

        if user == ctx.author:
            return await ctx.embed(lang["multi.error.sameuser"])

        gifs = self.gifData['pat']
        gif = random.choice(gifs)

        embed = std.getEmbed(lang["pat.message"].fomat(u1=ctx.author.mention, u2=user.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def hug(self, ctx: context.Context, user: discord.Member):
        lang = await ctx.lang()

        if user == ctx.author:
            return await ctx.embed(lang["multi.error.sameuser"])

        gifs = self.gifData['hug']
        gif = random.choice(gifs)

        embed = std.getEmbed(lang["hug.message"].fomat(u1=ctx.author.mention, u2=user.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def highfive(self, ctx: context.Context, user: discord.Member):
        lang = await ctx.lang()

        if user == ctx.author:
            return await ctx.embed(lang["multi.error.sameuser"])

        gifs: list[str] = self.gifData['highfive']
        gif = random.choice(gifs)

        embed = discord.Embed(color=std.normal_color, description=lang["highfive.message"].format(u1=ctx.author.mention, u2=user.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def rage(self, ctx: context.Context):
        lang = await ctx.lang()

        gifs: list[str] = self.gifData['rage']
        gif = random.choice(gifs)

        embed = std.getEmbed(lang["rage.message"].format(u=ctx.author.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def cry(self, ctx: context.Context):
        lang = await ctx.lang()

        gifs: list[str] = self.gifData['cry']
        gif = random.choice(gifs)

        embed = std.getEmbed(lang["cry.message"].format(u=ctx.author.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd(name='8ball')
    @checks.isActive('fun')
    async def _8ball(self, ctx: context.Context, *, Frage: str):
        lang = await ctx.lang()
        await ctx.embed(f'> {Frage}\n{random.choice(lang["8ball.answers"])}', allowed_mentions=discord.AllowedMentions.none(), signed=True)

    @cmd()
    @checks.isActive('fun')
    async def cat(self, ctx: context.Context):
        gifs: list[str] = self.gifData['cat']
        gif = random.choice(gifs)

        embed = discord.Embed(color=std.normal_color)
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def laugh(self, ctx: context.Context):
        lang = await ctx.lang()

        gifs: list[str] = self.gifData['laugh']
        gif = random.choice(gifs)

        embed = std.getEmbed(lang["laugh.message"].format(u=ctx.author.mention))
        embed.set_image(url=gif)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
