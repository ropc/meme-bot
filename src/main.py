import io
import os
import re
import uuid
import discord
import textwrap
import memes
from typing import Dict
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


client = discord.Client()

memeloader = memes.MemeLoader([
    memes.spongebob_config,
    memes.mouthfeel_config,
    memes.change_my_mind_config
])

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

        meme_name, meme_text = parsed_message

        meme_generator: memes.BaseMeme = memeloader.get(meme_name)
        if meme_generator is None:
            print('idk message')
            return await send_failure(message.channel)
        # do something
        return await handle_meme(meme_text, meme_generator, message.channel)


async def handle_meme(meme_text, meme_generator: memes.BaseMeme, channel: discord.TextChannel):
    meme_image_path = meme_generator.generate(meme_text)

    with open(meme_image_path, 'rb') as f:
        await channel.send(file=discord.File(f))

    os.remove(meme_image_path)  # cleanup


def parse_message(message_content: str):
    split_message = message_content.split(' ')
    if len(split_message) < 2:
        return None

    meme_name = split_message[1]
    meme_text = ' '.join(split_message[2:])

    return (meme_name, meme_text)


async def send_failure(channel: discord.TextChannel):
    return await channel.send("I don't know that meme =(")


client.run(os.getenv('MEME_BOT_TOKEN'))
