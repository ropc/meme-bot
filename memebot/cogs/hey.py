import discord
from discord.ext import commands

class Hey(commands.Cog):

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.content.lower() != 'hey':
            return

        await message.add_reaction('👋')
