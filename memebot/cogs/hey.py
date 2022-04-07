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

        attachment = self.ooc_cog.get_random_ooc_attachment(message.guild.id) if message.guild else None
        if not attachment:
            return

        attachment_file = await attachment.to_file()
        await message.channel.send(file=attachment_file)
