import asyncio
import re
import discord
from dataclasses import dataclass
from typing import Callable, Optional
from discord.ext import commands


@dataclass
class SearchParams:
    channel_id: int
    message_id: int


ChannelProvider = Callable[[int], Optional[discord.Message]]


class Quote(commands.Cog):

    @commands.command()
    async def quote(self, context: commands.Context, arg: str):
        '''Quote a message. Usage: !quote <message id or message link>'''
        searches = []
        if (match := re.match(r'https?://discord(app)?\.com/channels/(\d+)/(\d+)/(\d+)', arg)):
            searches.append(SearchParams(
                channel_id=int(match.group(3)),
                message_id=int(match.group(4))
            ))
        else:
            message_id = int(arg)
            searches.extend(SearchParams(channel_id=c.id, message_id=message_id) for c in context.channel.guild.text_channels)

        search_results = await asyncio.gather(*[fetch_message(context.bot.get_channel, sp.channel_id, sp.message_id) for sp in searches])
        found_messages = [x for x in search_results if x]
        if len(found_messages) == 0:
            return await context.send(f'Could not find message with id {message_id!r}')

        await context.send(embed=format_quote_embed(found_messages[0]))


async def fetch_message(channel_provider: ChannelProvider, channel_id: int, message_id: int) -> Optional[discord.Message]:
    if (quote_channel := channel_provider(channel_id)) is None:
        return None

    try:
        return await quote_channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden):
        return None


def format_quote_embed(message: discord.Message):
    quoted_content = '> ' + message.content.replace('\n', '\n> ')
    embed = discord.Embed(
        title=f'Link to message',
        description=f'{quoted_content}\n - {message.author.name} in {message.channel.mention}',
        url=create_message_link(message))
    embed.set_footer(text='Quote brought you by MORM-BET, the most reputable source for quotes. [citation needed]')
    return embed


def create_message_link(message: discord.Message):
    return f'https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'
