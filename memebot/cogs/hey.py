import discord
from discord.ext import commands
from .outofcontext import OutOfContext

class Hey(commands.Cog):

    def __init__(self, ooc_cog: OutOfContext):
        super().__init__()
        self.ooc_cog = ooc_cog

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.content.lower() != 'hey':
            return

        await message.add_reaction('👋')
        # await self.ooc_cog.send_ooc_message(message.channel)
