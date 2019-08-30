import os
import traceback
import attr
import discord
from pygtrie import CharTrie
from typing import Dict, List, Callable, Awaitable
from memes import Meme, ALL_MEMES


@attr.s(frozen=True, kw_only=True)
class ParsedCommand:
    name: str = attr.ib()
    arg: str = attr.ib()
    executor: Callable[[str, discord.abc.Messageable], Awaitable[None]] = attr.ib()

    async def execute(self, messageable: discord.abc.Messageable):
        #pylint: disable=not-callable
        return await self.executor(self.arg, messageable)


class MemeBot(discord.Client):

    def __init__(self, *, known_memes: List[Meme]):
        super().__init__()

        # commands setup
        self.commands = CharTrie()
        # meme aliases
        for meme in known_memes:
            executor = create_meme_executor(meme)
            for alias in meme.aliases:
                self.commands[f'!meme {alias}'] = executor
        # meme list
        aliases = ', '.join(m.aliases[0] for m in known_memes)
        memelist_command_executor = create_text_response_executor(f'I know these memes: {aliases}')
        self.commands['!meme list'] = memelist_command_executor
        self.commands['!memelist'] = memelist_command_executor

    async def on_ready(self):
        print(f'We have logged in as {self.user}')

    async def on_message(self, message: discord.Message):
        print(f'received message from {message.author.name}')
        if message.author == self.user:
            return

        if message.content.startswith('!meme'):
            await self.respond_to_message(message)

    async def respond_to_message(self, message: discord.Message):
        async with message.channel.typing():
            parsed_command = self.parse_message(message.content)

            if parsed_command is None:
                print('bad message')
                return await self.send_failure(message.channel)

            return await parsed_command.execute(message.channel)
    
    async def send_failure(self, channel: discord.abc.Messageable):
        return await channel.send("I don't know that command =(")
    
    def parse_message(self, message_content: str) -> ParsedCommand:
        command_name, command_executor = self.commands.longest_prefix(message_content)
        if command_name is None:
            return None

        command_arg = message_content[len(command_name):].strip()

        return ParsedCommand(name=command_name, arg=command_arg, executor=command_executor)


def create_meme_executor(meme_generator: Meme):
    async def run_meme(command_arg, channel: discord.abc.Messageable):
        try:
            meme_image_path = await meme_generator.generate(command_arg)
            with open(meme_image_path, 'rb') as f:
                message = await channel.send(file=discord.File(f))
            os.remove(meme_image_path)  # cleanup
            return message
        except Exception:
            traceback.print_exc()
            return await channel.send('Something went wrong when trying to send your meme =(')
    return run_meme


def create_text_response_executor(text: str):
    async def send_text(command_arg, channel: discord.abc.Messageable):
        return await channel.send(text)
    return send_text


if __name__ == "__main__":
    bot = MemeBot(known_memes=ALL_MEMES)
    bot.run(os.getenv('MEME_BOT_TOKEN'))
