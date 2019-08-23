import os
import discord
from pygtrie import CharTrie
from typing import Dict, List
from memes import Meme, ALL_MEMES


class MemeBot(discord.Client):

    def __init__(self, *, known_memes: List[Meme], **options):
        super().__init__(self, **options)

        # commands setup
        self.commands = CharTrie()
        for meme in known_memes:
            self.commands[f'!meme {meme.alias}'] = create_meme_executor(meme)
    
        aliases = ', '.join(m.aliases[0] for m in known_memes)
        self.commands['!meme list'] = create_text_response_executor(f'I know these memes: {aliases}')

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
            parsed_message = self.parse_message(message.content)
            if parsed_message is None:
                print('bad message')
                return await self.send_failure(message.channel)

            _, command_arg, command_executor = parsed_message

            return await command_executor(command_arg, message.channel)
    
    async def send_failure(self, channel: discord.TextChannel):
        return await channel.send("I don't know that command =(")
    
    def parse_message(self, message_content: str):
        command_name, command_executor = self.commands.longest_prefix(message_content)
        if command_name is None:
            return None

        command_arg = message_content[len(command_name):].strip()

        return (command_name, command_arg, command_executor)


def create_meme_executor(meme_generator: Meme):
    async def run_meme(command_arg, channel: discord.TextChannel):
        try:
            meme_image_path = meme_generator.generate(command_arg)
            with open(meme_image_path, 'rb') as f:
                await channel.send(file=discord.File(f))
            os.remove(meme_image_path)  # cleanup
        except Exception as e:
            print(e)
            await channel.send('Something went wrong when trying to send your meme =(')
    return run_meme


def create_text_response_executor(text: str):
    async def send_text(command_arg, channel: discord.TextChannel):
        return await channel.send(text)
    return send_text


if __name__ == "__main__":
    bot = MemeBot(known_memes=ALL_MEMES)
    bot.run(os.getenv('MEME_BOT_TOKEN'))
