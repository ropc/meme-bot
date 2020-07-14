import discord
import pygtrie
from discord.ext import commands
from meme_generator import ALL_MEMES, Meme as MemeGenerator


class MemeGroup(commands.Group):
    def __init__(self, *args, **attrs):
        super().__init__(*args, **attrs)
        self.all_commands = pygtrie.CharTrie(self.all_commands)


class Meme(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.meme.all_commands = pygtrie.CharTrie(self.meme.all_commands)

        for meme_generator in ALL_MEMES:
            _create_meme_command(self.meme, meme_generator)

    @commands.group(cls=MemeGroup, aliases=['memelist', 'meme list'])
    async def meme(self, context: commands.Context):
        '''list memes'''
        if not context.invoked_subcommand:
            return await context.send_help(self.meme)


def _create_meme_command(group: commands.Group, meme_generator: MemeGenerator):
    generator_name = meme_generator.aliases[0].replace(' ', '_') + '_executor'
    @group.command(help=meme_generator.help_string, name=generator_name, aliases=meme_generator.aliases)
    async def meme_executor(context: commands.Context, *, text: str):
        async with context.typing():
            async with meme_generator.generate(text) as meme_image:
                df = discord.File(meme_image, filename=meme_generator.image_filename)
                return await context.send(file=df)
