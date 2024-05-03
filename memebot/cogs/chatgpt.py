import discord
import logging
from discord.ext import commands
from openai import OpenAI
from typing import Optional, List, Iterable
from .outofcontext import OutOfContext

log = logging.getLogger('memebot')

class ChatGPT(commands.Cog):

    def __init__(self, bot_id: int, allowed_guilds: Iterable[int]):
        super().__init__()
        self.bot_id = bot_id
        self.client = OpenAI()
        self.allowed_guilds = set(allowed_guilds)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild and message.guild.id not in self.allowed_guilds:
            return
        replied_message = await self.get_replied_message(message)
        bot_was_replied = replied_message and replied_message.author.id == self.bot_id
        bot_was_mentioned = len(message.mentions) == 1 and message.mentions[0].id == self.bot_id
        if not (bot_was_mentioned or bot_was_replied):
            return

        async with message.channel.typing():
            message_history = [m async for m in self.get_reply_history(message)]

            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.format_chatgpt_message_history(message_history)
            )

            log.debug("chatgpt api response: %s", completion)
            chatgpt_response = completion.choices[0].message.content
            await paginated_reply(message, chatgpt_response)

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

    def format_chatgpt_message_history(self, message_history: Iterable[discord.Message]):
        simple_formatted_messages = [self.format_chatgpt_message(m) for m in message_history]
        new_messages = [simple_formatted_messages.pop(0)] if len(simple_formatted_messages) > 0 else []
        for message in simple_formatted_messages:
            prev_message_role: str = new_messages[-1]['role']
            prev_message_content: str = new_messages[-1]['content']
            if (prev_message_role == 'assistant'
                and message['role'] == 'assistant'
                and prev_message_content.endswith('...')):
                new_messages[-1]['content'] = prev_message_content[:-3] + message['content']
            else:
                new_messages.append(message)
        return new_messages

    def format_chatgpt_message(self, message: discord.Message):
        return {
            'role': 'assistant' if message.author.id == self.bot_id else 'user',
            'content': message.content.replace(f'<@{self.bot_id}>', 'ChatGPT'),
        }

async def paginated_reply(message: discord.Message, text: str):
    if len(text) <= 2000:
        return await message.reply(text)

    new_message = await message.reply(text[:1997] + '...')
    await paginated_reply(new_message, text[1997:])
