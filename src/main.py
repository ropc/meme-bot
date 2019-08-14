import io
import os
import re
import uuid
import discord
import textwrap
from memes import Meme, ALL_MEMES
from pygtrie import CharTrie
from typing import Dict
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


client = discord.Client()

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

# commands setup
commands = CharTrie()
for meme in ALL_MEMES:
    commands[f'!meme {meme.alias}'] = create_meme_executor(meme)
aliases = ', '.join(m.alias for m in ALL_MEMES)
commands['!meme list'] = create_text_response_executor(f'I know these memes: {aliases}')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    print(message)
    if message.author == client.user:
        return

    if is_talking_to_bot(message.content):
        await respond_to_message(message)


def is_talking_to_bot(message_content: str) -> bool:
    return message_content.startswith('!meme')


async def respond_to_message(message: discord.Message):
    async with message.channel.typing():
        parsed_message = parse_message(message.content)
        if parsed_message is None:
            print('bad message')
            return await send_failure(message.channel)

        _, command_arg, command_executor = parsed_message

        return await command_executor(command_arg, message.channel)


def parse_message(message_content: str):
    command_name, command_executor = commands.longest_prefix(message_content)
    if command_name is None:
        return None

    command_arg = message_content[len(command_name):].strip()

    return (command_name, command_arg, command_executor)


async def send_failure(channel: discord.TextChannel):
    return await channel.send("I don't know that command =(")


client.run(os.getenv('MEME_BOT_TOKEN'))
