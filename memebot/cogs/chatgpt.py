import discord
import logging
from discord.ext import commands
from openai import OpenAI
from typing import Optional, List
from .outofcontext import OutOfContext

log = logging.getLogger('memebot')

class ChatGPT(commands.Cog):

    def __init__(self, bot_id: int):
        super().__init__()
        self.bot_id = bot_id
        self.client = OpenAI()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        replied_message = await self.get_replied_message(message)
        bot_was_replied = replied_message and replied_message.author.id == self.bot_id
        bot_was_mentioned = len(message.mentions) == 1 and message.mentions[0].id == self.bot_id
        if not (bot_was_mentioned or bot_was_replied):
            return

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[self.format_chatgpt_message(m) for m in message_history]
        )

        log.debug("chatgpt api response: %s", completion)
        chatgpt_response = completion.choices[0].message.content
        await message.reply(chatgpt_response)

    async def get_reply_history(self, message: discord.Message):
        replied_message = await self.get_replied_message(message)
        if not replied_message:
            yield message
            return

        async for previous_message in self.get_reply_history(replied_message):
            yield previous_message
        yield message

    async def get_replied_message(self, message: discord.Message) -> Optional[discord.Message]:
        if not message.reference:
            return None
        return message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)

    def format_chatgpt_message(self, message: discord.Message):
        return {
            'role': 'system' if message.author.id == self.bot_id else 'user',
            'content': message.content.replace(f'<@{self.bot_id}>', 'ChatGPT'),
        }
