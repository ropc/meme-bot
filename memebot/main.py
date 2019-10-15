import os
import random
import logging as log
import attr
import discord
from pygtrie import CharTrie
from typing import Dict, List, Callable, Awaitable, Optional
from memes import Meme, ALL_MEMES


log.basicConfig(format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s')


@attr.s(frozen=True, kw_only=True)
class Command:
    name: str = attr.ib()
    arg: str = attr.ib()
    executor: Callable[[str, discord.abc.Messageable], Awaitable[None]] = attr.ib()
    raw_command: str = attr.ib()

    async def execute(self, messageable: discord.abc.Messageable):
        try:
            #pylint: disable=not-callable
            return await self.executor(self.arg, messageable)
        except Exception:
            log.exception(f'error when executing command "{self.raw_command}"')
            await messageable.send('Something went wrong =(')


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
        self.commands['!r'] = roll_dice
        self.commands['!roll'] = roll_dice

    async def on_ready(self):
        log.info(f'We have logged in as {self.user}')

    async def on_message(self, message: discord.Message):
        log.info(f'received message from {message.author.name}')
        if message.author == self.user:
            return

        command = self.parse_message(message.content)
        if command:
            await command.execute(message.channel)

    def parse_message(self, message_content: str) -> Optional[Command]:
        command_name, command_executor = self.commands.longest_prefix(message_content)
        if command_name is None:
            return None

        command_arg = message_content[len(command_name):].strip()

        return Command(name=command_name, arg=command_arg,
            executor=command_executor, raw_command=message_content)


def create_meme_executor(meme_generator: Meme):
    async def run_meme(command_arg, channel: discord.abc.Messageable):
        async with meme_generator.generate(command_arg) as meme_image:
            df = discord.File(meme_image, filename=meme_generator.image_filename)
            return await channel.send(file=df)
    return run_meme


def create_text_response_executor(text: str):
    async def send_text(command_arg, channel: discord.abc.Messageable):
        return await channel.send(text)
    return send_text

async def roll_dice(command_arg, channel: discord.abc.Messageable):
    num_dice, num_sides = [int(x) for x in command_arg.split('d')]

    # soft limit. (2k - 16) hardcoded characters in message
    if num_dice * num_sides.bit_length() > 1984:
        return await channel.send("I don't have all those dice")

    raw_rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(raw_rolls)
    formatted_rolls = ', '.join(str(r) for r in raw_rolls)
    message = f'Total: {total}, rolls: {formatted_rolls}'

    if len(message) > 2000:  # discord has a 2k message limit
        return await channel.send("I don't have all those dice")

    return await channel.send(message)


if __name__ == "__main__":
    bot = MemeBot(known_memes=ALL_MEMES)
    bot.run(os.getenv('MEME_BOT_TOKEN'))
