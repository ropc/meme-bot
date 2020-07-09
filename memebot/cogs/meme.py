import discord
import pygtrie
from discord.ext import commands
from meme_generator import ALL_MEMES, Meme as MemeGenerator


class Meme(commands.Cog):

    def __init__(self):
        super().__init__()
        self.meme_generators = pygtrie.CharTrie()

        for meme_generator in ALL_MEMES:
            for alias in meme_generator.aliases:
                self.meme_generators[alias] = meme_generator

    @commands.command()
    async def meme(self, context: commands.Context, *, text: str):
        meme_alias, meme_generator = self.meme_generators.longest_prefix(text)
        if meme_alias is None:
            return await context.send("i don't know that meme")

        meme_text = text[len(meme_alias):].strip()

        async with context.typing():
            async with meme_generator.generate(meme_text) as meme_image:
                df = discord.File(meme_image, filename=meme_generator.image_filename)
                return await context.send(file=df)
