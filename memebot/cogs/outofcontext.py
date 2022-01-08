import random
import discord
from discord.ext import commands
from typing import MutableSequence


class OutOfContext(commands.Cog):

    def __init__(self, bot: commands.Bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.attachments: MutableSequence[discord.Attachment] = []

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        attachments: MutableSequence[discord.Attachment] = []
        async for message in channel.history(limit=10_000):
            attachments.extend(message.attachments)
        self.attachments = attachments

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != self.channel_id or message.author.bot:
            return
        self.attachments.extend(message.attachments)

    @commands.command(aliases=['out of context', 'ooc'])
    async def out_of_context(self, context: commands.Context):
        '''Posts a random image from out of context channel'''
        return await self.send_ooc_message(context)

    async def send_ooc_message(self, messageable: discord.abc.Messageable):
        ooc_channel = self.bot.get_channel(self.channel_id)
        if not ooc_channel:
            return await messageable.send('Could not find out of context channel')

        if len(self.attachments) == 0:
            return await messageable.send('No images to send')

        async with messageable.typing():
            random_attachment = random.choice(self.attachments)
            attachment_file = await random_attachment.to_file()
            await messageable.send(file=attachment_file)
