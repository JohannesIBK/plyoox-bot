import argparse
import json
import random
import shlex

import discord
from discord.ext import commands

import main
from utils.ext import checks, standards as std, context
from utils.ext.cmds import cmd


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class Fun(commands.Cog):
    with open('utils/json/gif_links.json', encoding='utf-8') as gifs:
        gifData = json.load(gifs)

    def __init__(self, bot: main.Plyoox):
        self.bot = bot

    # --------------------------------commands--------------------------------

    @cmd()
    @checks.isActive('fun')
    async def color(self, ctx: context.Context):
        rgbs = []
        for _ in range(0, 3, 1):
            rgbs.append(random.choice(range(256)))
        color = discord.Colour.from_rgb(rgbs[0], rgbs[1], rgbs[2])
        colorHex = "#%02x%02x%02x" % (rgbs[0], rgbs[1], rgbs[2])
        await ctx.send(embed=discord.Embed(color=color,
                                           description=f'Es wurde eine zufällige Farbe generiert:\nFarbcode in RGB {rgbs} und HEX-Code {colorHex}'))

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
        if user2 is None:
            user2 = ctx.message.author

        if user1 == user2:
            return ctx.embed('Das funktioniert so nicht D:')

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
        if 'discord.gg' in questions.lower() or 'discord.com/invite' in questions.lower():
            return
        if questions.count('|') == 0:
            return await ctx.error('Fargen müssen mit `|` getrennt werden')

        questionsList = questions.split('|')
        choosen: str = random.choice(questionsList)
        await ctx.send(f'Ich wähle: `{choosen.strip()}`', allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

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
        emojis = ("🍎", '🍉', '🍇', '🍓', '🍒')

        selected = ''
        for _ in range(3):
            selected += random.choice(emojis)
        rolled = len(set(selected))

        if rolled == 1:
            await ctx.send(f"{''.join(selected)} Du hast gewonnen! 🎉")
        else:
            await ctx.send(f"{''.join(selected)} Verloren 😢")

    @cmd()
    @checks.isActive('fun')
    async def reverse(self, ctx: context.Context, *, text: str):
        reversedText = text[::-1]
        if 'discord.gg' in reversedText.lower() or 'discord.com/invite' in reversedText.lower():
            return

        embed = std.getEmbed(reversedText)
        embed.set_footer(icon_url=ctx.author.avatar_url, text=ctx.author)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def caseing(self, ctx: context.Context, *, text: str):
        if 'discord.gg' in text.lower() or 'discord.com/invite' in text.lower():
            return
        newText = []
        lastUpper = False

        for word in text.split(" "):
            t = ""
            for i in range(len(word)):
                char = word[i]
                if not lastUpper:
                    t += char.upper()
                    lastUpper = True
                else:
                    t += char.lower()
                    lastUpper = False
            newText.append(t)

        embed: discord.Embed = std.getEmbed(' '.join(newText)) 
        embed.set_footer(icon_url=ctx.author.avatar_url, text=ctx.author)
        await ctx.send(embed=embed)

    @cmd(aliases=['ts'])
    @checks.isActive('fun')
    async def twitchsings(self, ctx: context.Context, *, args):
        parser = Arguments()
        parser.add_argument('--lang', '-l')
        parser.add_argument('--year', '-y', type=int)
        parser.add_argument('--range', type=int)
        parser.add_argument('--genre')
        parser.add_argument('--name')
        parser.add_argument('--same', type=bool, default=False)
        parser.add_argument('--by')
        parser.add_argument('--count', type=int)

        try:
            argsParsed = parser.parse_args(shlex.split(args))
        except Exception as e:
            return await ctx.send(str(e))


        with open('utils/json/songs.json') as songFile:
            songs = json.load(songFile)

        if lang := argsParsed.lang:
            songs = [song for song in songs if song['lang'] == lang.lower()]

        if year := argsParsed.year:
            if yearRange := argsParsed.range:
                songs = [song for song in songs if abs(song['year'] - year) <= yearRange]
            else:
                songs = [song for song in songs if song['year'] == year]

        if by := argsParsed.by:
            songs = [song for song in songs if by.lower() in song['by'].lower()]

        if genre := argsParsed.genre:
            songs = [song for song in songs if genre.lower() in song['genres']]

        if name := argsParsed.name:
            if argsParsed.same:
                songs = [song for song in songs if name == song['song']]
            else:
                songs = [song for song in songs if name.lower() in song['song'].lower()]

        if count := argsParsed.count:
            if count == 0:
                songs = []
            else:
                songs = songs[:count]

        songStr = '\n'.join(f'`{song["by"]}` | `{song["song"]}` | `{song["year"]}`' for song in songs)
        if songStr == '':
            songStr = 'Keine Songs gefunden :('
        await ctx.embed(songStr[:2000])

    @cmd()
    @checks.isActive('fun')
    async def pat(self, ctx: context.Context, user: discord.Member):
        if user == ctx.author:
            return ctx.embed('Das funktioniert so nicht D:')

        gifs = self.gifData['pat']
        gif = random.choice(gifs)

        embed = std.getEmbed('{ctx.author.mention} patted {user.mention}')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def hug(self, ctx: context.Context, user: discord.Member):
        if user == ctx.author:
            return ctx.embed('Das funktioniert so nicht D:')

        gifs = self.gifData['hug']
        gif = random.choice(gifs)

        embed = std.getEmbed('{ctx.author.mention} hugged {user.mention}')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def highfive(self, ctx: context.Context, user: discord.Member):
        if user == ctx.author:
            return ctx.embed('Das funktioniert so nicht D:')

        gifs: list = self.gifData['highfive']
        gif: str = random.choice(gifs)

        embed: discord.Embed = discord.Embed(color=std.normal_color,
                                             description=f'{ctx.author.mention} gives {user.mention} a highfive')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def rage(self, ctx: context.Context):
        gifs: list = self.gifData['rage']
        gif: str = random.choice(gifs)

        embed = std.getEmbed('{ctx.author.mention} rages')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def cry(self, ctx: context.Context):
        gifs: list = self.gifData['cry']
        gif: str = random.choice(gifs)

        embed = std.getEmbed('{ctx.author.mention} cries')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd(name='8ball')
    @checks.isActive('fun')
    async def _8ball(self, ctx: context.Context, *, Frage: str):
        answers = [
            'Ja.',
            'Kann sein.',
            'Auf jeden Fall!',
            'Niemals!',
            'Nein.',
            'Vermutlich.',
            'So wie ich das sehe, ja.',
            'Das kann ich jetzt noch nicht sagen.',
            'Ich sage nein.',
            'Meine Quellen sagen nein.',
            'Das sage ich dir besser nicht.',
            'Schaut schlecht aus',
            'Ja, auf jeden Fall!',
            'Ich kann mich nicht entscheiden.',
            'Die Sterne schauen gut aus.',
            'Lass mich kurz nachdenken... Nein.',
            'Lass mich kurz nachdenken... Ja.',
            'Ich denke, ich kann dir das nicht sagen.',
            'Meine Antwort ist ja.',
            'Meine Antwort ist nein.',
            'Ich bin mir unsicher.'
        ]
        await ctx.send(f'> {Frage}\n{random.choice(answers)}', allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @cmd()
    @checks.isActive('fun')
    async def cat(self, ctx: context.Context):
        gifs: list = self.gifData['cat']
        gif: str = random.choice(gifs)

        embed: discord.Embed = discord.Embed(color=std.normal_color)
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

    @cmd()
    @checks.isActive('fun')
    async def laugh(self, ctx: context.Context):
        gifs: list = self.gifData['laugh']
        gif: str = random.choice(gifs)

        embed = std.getEmbed(f'{ctx.author.mention} laughs')
        embed.set_image(url=gif)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
