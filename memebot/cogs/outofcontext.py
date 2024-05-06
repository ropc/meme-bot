import asyncio
import logging
import os.path
import random
import discord
from dataclasses import dataclass
from pydantic import BaseModel
from discord.ext import commands
from typing import List, Dict, Optional


log = logging.getLogger('memebot')


@dataclass
class MessageAttachment:
    message_id: int
    attachment_id: int

    @staticmethod
    def from_message(message: discord.Message):
        for attachment in message.attachments:
            yield MessageAttachment(message_id=message.id, attachment_id=attachment.id)


class Config(BaseModel):
    guild_ooc_channel_id: Dict[int, int]  # guild_id to channel_id


class OutOfContext(commands.Cog):

    def __init__(self, bot: commands.Bot, config_filepath: str):
        super().__init__()
        self.bot = bot
        self.config_filepath = config_filepath
        self.config = load_config(config_filepath)
        self.guild_attachments: Dict[int, List[MessageAttachment]] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.gather(*[self.load_attachments(guild_id, channel_id) for (guild_id, channel_id) in self.config.guild_ooc_channel_id.items()])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_ooc_channel_id = self.config.guild_ooc_channel_id.get(message.guild.id)
        if not guild_ooc_channel_id or message.channel.id != guild_ooc_channel_id:
            return

        if message.guild.id not in self.guild_attachments.keys():
            log.warning(f'could not find guild {message.guild.id} in guild_attachments dict.'
                + 'maybe received message before completed loading old messages?')
            return

        self.guild_attachments[message.guild.id].extend(MessageAttachment.from_message(message))

    @commands.Cog.listener()
    async def on_raw_message_delete(self, event: discord.RawMessageDeleteEvent):
        if not event.guild_id:
            return

        guild_ooc_channel_id = self.config.guild_ooc_channel_id.get(event.guild_id)
        if not guild_ooc_channel_id or event.channel_id != guild_ooc_channel_id:
            return

        to_delete_indexes = []
        for (idx, message_attachment) in enumerate(self.guild_attachments[event.guild_id]):
            if message_attachment.message_id != event.message_id:
                continue
            to_delete_indexes.append(idx)

        # reversed iteration to prevent indexes from shifting from use of .pop()
        for index in reversed(to_delete_indexes):
            self.guild_attachments[event.guild_id].pop(index)

    @commands.command(aliases=['out of context', 'ooc'])
    @commands.guild_only()
    async def out_of_context(self, context: commands.Context):
        '''Posts a random image from out of context channel'''
        channel_id = self.config.guild_ooc_channel_id.get(context.guild.id)
        if not channel_id:
            return await context.send('no ooc channel set up for this server')

        ooc_channel = context.bot.get_channel(channel_id)
        if not ooc_channel:
            return await context.send('Could not find out of context channel')

        random_attachment = await self.get_random_ooc_attachment(context.guild.id)
        if not random_attachment:
            return await context.send('No images to send')

        async with context.typing():
            attachment_file = await random_attachment.to_file()
            await context.send(file=attachment_file)

    @commands.command(aliases=['set ooc channel'])
    @commands.guild_only()
    @commands.is_owner()
    async def set_ooc_channel(self, context: commands.Context, channel: discord.TextChannel):
        self.config.guild_ooc_channel_id[channel.guild.id] = channel.id
        with open(self.config_filepath, 'w+') as f:
            f.write(self.config.json())

        message: discord.Message = await context.send(f'set ooc channel as {channel.mention}. loading attachments')
        attachments = await self.load_attachments(channel.guild.id, channel.id)
        await message.edit(content=f'set ooc channel as {channel.mention}. loaded {len(attachments)} attachments')

    async def load_attachments(self, guild_id: int, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        message_attachments = []
        async for message in channel.history(limit=10_000):
            message_attachments.extend(MessageAttachment.from_message(message))

        self.guild_attachments[guild_id] = message_attachments
        return message_attachments

    async def get_random_ooc_attachment(self, guild_id: int) -> Optional[discord.Attachment]:
        message_attachments = self.guild_attachments.get(guild_id)
        if not message_attachments or len(message_attachments) == 0:
            return None

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None

        ooc_channel = guild.get_channel(self.config.guild_ooc_channel_id[guild_id])
        if not ooc_channel or not isinstance(ooc_channel, discord.TextChannel):
            return None

        message_attachment = random.choice(message_attachments)
        message = await ooc_channel.fetch_message(message_attachment.message_id)
        return next(attachment for attachment in message.attachments if attachment.id == message_attachment.attachment_id)


def load_config(filepath: str):
    if not os.path.isfile(filepath):
        return Config(guild_ooc_channel_id={})
    try:
        config = Config.parse_file(filepath)
        log.debug(f'loaded ooc config: {config}')
        return config
    except KeyError:
        raise
    except:
        log.exception('error loading ooc config')
        return Config(guild_ooc_channel_id={})
