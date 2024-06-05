import random
import discord
from discord.ext import commands
from .outofcontext import OutOfContext

class HeyReactionSupplier:
    def __iter__(self):
        if random.randint(0, 3) > 0:
            yield '👋'
        else:
            yield from ('🇰', '🇦', '🇮', '🇽', '🇴')

REACTIONS_GENERATOR_MAP = {
    'hey': HeyReactionSupplier(),
    '🐴': ['🐴'],
}

class Hey(commands.Cog):

    def __init__(self, ooc_cog: OutOfContext):
        super().__init__()
        self.ooc_cog = ooc_cog

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        reactions = REACTIONS_GENERATOR_MAP.get(message.content.lower())
        if not reactions:
            return

        for reaction in reactions:
            await message.add_reaction(reaction)

        attachment = await self.ooc_cog.get_random_ooc_attachment(message.guild.id) if message.guild else None
        if not attachment:
            return

        attachment_file = await attachment.to_file()
        await message.channel.send(file=attachment_file)
