import re
import discord
from .command import executor, UserCommand


def format_quote_embed(message: discord.Message):
    quoted_content = '> ' + message.content.replace('\n', '\n> ')
    embed = discord.Embed(
        title=f'Link to message',
        description=f'{quoted_content}\n - {message.author.name} in #{message.channel.name}',
        url=create_message_link(message))
    embed.set_footer(text='Quote brought you by MORM-BET, the most reputable source for quotes. [citation needed]')
    return embed


def create_message_link(message: discord.Message):
    return f'https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'


def create_quote_executor(client: discord.Client):
    @executor()
    async def quote(command: UserCommand, channel: discord.TextChannel):
        '''Quote a message. Usage: !quote <message id or message link>'''
        if (match := re.match(r'https?://discord(app)?\.com/channels/(\d+)/(\d+)/(\d+)', command.arg)):
            guild_id = int(match.group(2))
            channel_id = int(match.group(3))
            message_id = int(match.group(4))
        else:
            guild_id = channel.guild.id
            channel_id = channel.id
            message_id = int(command.arg)

        if (quote_channel := client.get_channel(channel_id)) is None:
            return await channel.send(f'Cound not find channel with id {channel_id!r}')

        try:
            message = await quote_channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            return await channel.send(f'Could not find message with id {message_id!r}')

        await channel.send(embed=format_quote_embed(message))
    return quote
