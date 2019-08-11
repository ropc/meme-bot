import io
import os
import uuid
import discord
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

client = discord.Client()

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

        # yeah, this is gross
        if meme_name.lower() == 'spongebob':
            # do something
            return await send_spongebob_meme(meme_text, message.channel)
            
        print('idk message')
        return await send_failure(message.channel)


def parse_message(message_content: str):
    split_message = message_content.split(' ')
    if len(split_message) < 2:
        return None

    meme_name = split_message[1]
    meme_text = ''.join(split_message[2:])

    return (meme_name, meme_text)


async def send_failure(channel: discord.TextChannel):
    return await channel.send("I don't know that meme =(")


async def send_spongebob_meme(meme_text: str, channel: discord.TextChannel):
    meme_image_path = f'spongebob-{uuid.uuid4()}.jpg'
    with open('spongebob.jpg', 'rb') as f:
        img = Image.open(io.BytesIO(f.read()))
        # buffer = io.BytesIO()
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype('Impact', 48)
        
        draw.text(((img.size[0] / 2), img.size[1] * 2 /3), meme_text, font=font)
        img.save(meme_image_path, format='JPEG')

    with open(meme_image_path, 'rb') as f:
        await channel.send(file=discord.File(f))
    
    os.remove(meme_image_path)  # cleanup


client.run(os.getenv('MEME_BOT_TOKEN'))
