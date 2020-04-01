import os
import random
import logging
import discord
import uuid
from pydantic import BaseModel
from pygtrie import CharTrie, Trie
from functools import wraps
from typing import Dict, Iterable, Set, Callable, Awaitable, Optional, MutableMapping, Tuple, Union, Mapping
from ..meme_generator import Meme, ALL_MEMES
from .command import Command, CommandExecutor, executor
from .player import Player, PlayerEvent, PlayerEventType, SearchEvent, SearchEventType
from .guildconfig import GuildConfig, get_guild_config

logging.basicConfig(format='%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s')

log = logging.getLogger('memebot')
log.setLevel(logging.INFO)



class PlayerConfig(BaseModel):
    player: Player
    voice_channel_id: int
    text_channel_id: int

    class Config:
        arbitrary_types_allowed = True


class MemeBot(discord.Client):

    def __init__(self, *, known_memes: Iterable[Meme], guild_config: str):
        super().__init__()
        # TODO: consolidate this and MEME_BOT token to a single config
        self.guild_config = guild_config

        self.guild_player_config: MutableMapping[int, PlayerConfig] = {}

        # commands setup
        self.commands = CharTrie()
        # meme aliases
        for meme in known_memes:
            executor = create_meme_executor(meme)
            for alias in meme.aliases:
                self.commands[f'!meme {alias}'] = executor
        # meme list
        memelist_command_executor = create_memelist_command_executor(known_memes)
        self.commands['!meme list'] = memelist_command_executor
        self.commands['!memelist'] = memelist_command_executor

        # dice roll
        self.commands['!r'] = roll_dice
        self.commands['!roll'] = roll_dice

        # player commands
        self.commands['!play'] = create_play_executor(self.guild_player_config.get)
        self.commands['!skip'] = create_skip_executor(self.guild_player_config.get)
        self.commands['!queue'] = create_show_queue_executor(self.guild_player_config.get)

        # help
        self.commands['!help'] = create_help_command_executor(self.commands)

    async def on_ready(self):
        log.info(f'We have logged in as {self.user}')
        await self.setup_voice()

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

    async def setup_voice(self):
        log.info('setting up voice channels')
        for guild in self.guilds:
            config = get_guild_config(self.guild_config, guild.id)
            if not config:
                log.debug(f"guild {guild.id} not found in bot's guilds")
                continue
            if guild.id in self.guild_player_config:
                log.warning(f'already have player config for guild {guild.id}')
                continue

            voice_channel: discord.VoiceChannel = self.get_channel(config.voice_channel_id)
            text_channel: discord.TextChannel = self.get_channel(config.text_channel_id)

            if not voice_channel or not text_channel:
                log.warning(f'could not get voice/text channels for guild {guild.id}. GuildConfig: {config}')
                continue

            log.debug(f'connecting to voice channel: {voice_channel.id}')
            voice_client: discord.VoiceClient = await voice_channel.connect()

            player = Player(voice_client=voice_client, on_event_cb=create_player_event_handler(text_channel))

            self.guild_player_config[guild.id] = PlayerConfig(
                player=player,
                voice_channel_id=config.voice_channel_id,
                text_channel_id=config.text_channel_id)

        log.info('done setting up voice channels')


PlayerConfigProvider = Callable[[int], Optional[PlayerConfig]]
PlayerCommandExecutor = Callable[[str, discord.TextChannel, PlayerConfig], Awaitable[None]]


def ignore_by_player_config_provider(player_config_provider: PlayerConfigProvider) -> Callable[[PlayerCommandExecutor], CommandExecutor]:
    """Decorator factory to ignore player commands on unsupported servers/channels
    Arguments:
        player_config_provider {Provider[PlayerConfig]} -- provides Player and PlayerConfig
            based on received message's guild id
    Returns:
        CommandExecutor -- That will execute the PlayerCommandExecutor when a message
            is received in the allowed channel
    """
    async def no_op_awaitable():
        pass

    def wrapper(func: PlayerCommandExecutor):
        @executor()
        @wraps(func)
        def wrapped(command_arg: str, channel: discord.TextChannel):
            config = player_config_provider(channel.guild.id)
            if not config:
                log.debug(f'could not find config for guild id {channel.guild.id}')
                return no_op_awaitable()
            if config.text_channel_id != channel.id:
                log.debug(f'player command in guild {channel.guild.id} did not come from PlayerConfig.text_channel_id {config.text_channel_id}')
                return no_op_awaitable()
            return func(command_arg, channel, config)
        return wrapped
    return wrapper


def create_play_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def play(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        '''search for a song and add to queue'''
        await player_config.player.enqueue(command_arg)
    return play


def create_skip_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def skip(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        '''skips current song, if one is playing'''
        await player_config.player.skip()
    return skip


def create_show_queue_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def show_queue(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        '''shows current queue'''
        if len(player_config.player.playback_queue) == 0:
            return await channel.send('Nothing in queue. Add a song with !play', delete_after=30)
        queue = '\n'.join(f'- {item.title}' for item in player_config.player.playback_queue)
        return await channel.send(f'Up next:\n{queue}', delete_after=30)
    return show_queue


def create_player_event_handler(text_channel: discord.TextChannel):
    # maps transaction_id to discord.Message. maybe overkill
    known_search_messages: MutableMapping[uuid.UUID, discord.Message] = {}

    async def player_event_handler(event: PlayerEvent):
        if event.event_type == PlayerEventType.ENQUEUED:
            await text_channel.send(f'Added to queue: {event.context.title}', delete_after=30)
        elif event.event_type == PlayerEventType.STARTED:
            await text_channel.send(f'Now playing: {event.context.title}', delete_after=(15 * 60))

    async def search_event_handler(event: SearchEvent):
        if event.event_type == SearchEventType.SEARCHING:
            message = await text_channel.send(f'Searching for "{event.keyword}"', delete_after=30)
            known_search_messages[event.transaction_id] = message
            return

        message = known_search_messages.pop(event.transaction_id, None)
        if message:
            await message.delete(delay=0)

        if event.event_type == SearchEventType.SEARCH_ERROR:
            await text_channel.send(f'Could not find "{event.keyword}"', delete_after=30)

    async def handler(event: Union[PlayerEvent, SearchEvent]):
        log.debug(f'player handler received event: {event}')
        if isinstance(event, PlayerEvent):
            await player_event_handler(event)
        else:
            await search_event_handler(event)
    return handler


def create_meme_executor(meme_generator: Meme) -> CommandExecutor:
    @executor(help_string=meme_generator.help_string)
    async def run_meme(command_arg: str, channel: discord.abc.Messageable):
        async with meme_generator.generate(command_arg) as meme_image:
            df = discord.File(meme_image, filename=meme_generator.image_filename)
            return await channel.send(file=df)
    return run_meme


def create_memelist_command_executor(memes: Iterable[Meme]) -> CommandExecutor:
    aliases = ', '.join(m.aliases[0] for m in memes)
    @executor()
    async def send_memelist(command_arg: str, channel: discord.abc.Messageable):
        '''lists all known memes'''
        return await channel.send(f'I know these memes: {aliases}', delete_after=30)
    return send_memelist


@executor()
async def roll_dice(command_arg: str, channel: discord.abc.Messageable):
    '''rolls dice. Example: !roll 5d6'''
    num_dice, num_sides = [int(x if x else 1) for x in command_arg.split('d')]

    # soft limit. (2k - 16) hardcoded characters in message
    if num_dice * num_sides.bit_length() > 1984:
        return await channel.send("I don't have all those dice", delete_after=30)

    raw_rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(raw_rolls)

    if len(raw_rolls) > 1:
        formatted_rolls = ', '.join(str(r) for r in raw_rolls)
        message = f'Total: {total}, rolls: {formatted_rolls}'
    else:
        message = f'Total: {total}'

    if len(message) > 2000:  # discord has a 2k message limit
        return await channel.send("I don't have all those dice", delete_after=30)

    return await channel.send(message)


def create_help_command_executor(commands: Trie) -> CommandExecutor:
    def format_command(aliases: Iterable[str], executor: CommandExecutor):
        formatted_aliases = ', '.join(aliases)
        return f'{formatted_aliases} - {executor.help_string()}'

    def inverted_commands_map(commands: Mapping[str, CommandExecutor]) -> Mapping[CommandExecutor, Iterable[str]]:
        '''assumes executors for each command are reused'''
        inverted_map: MutableMapping[CommandExecutor, Set[str]] = {}
        for (key, item) in commands.items():
            alias_set = inverted_map.get(item, set())
            alias_set.add(key)
            inverted_map[item] = alias_set
        return inverted_map

    @executor()
    async def help_command(command_arg: str, channel: discord.abc.Messageable):
        '''lists all commands'''
        if len(command_arg) == 0:
            commands_string = '\n'.join(format_command(aliases, executor) for (executor, aliases) in inverted_commands_map(commands).items())
            return await channel.send(f'known commands are:\n{commands_string}', delete_after=30)

        command_name = command_arg if command_arg.startswith('!') else f'!{command_arg}'
        alias, executor = commands.longest_prefix(command_name)

        # maybe the user didn't include '!meme'
        if not alias or not executor:
            alias, executor = commands.longest_prefix(f'!meme {command_name[1:]}')

        if not alias or not executor:
            return await channel.send(f"i don't know the command '{command_name}'", delete_after=30)
        return await channel.send(format_command([alias], executor), delete_after=30)
    return help_command


def run():
    bot = MemeBot(known_memes=ALL_MEMES, guild_config=os.getenv('MEME_BOT_GUILD_CONFIG'))
    bot.run(os.getenv('MEME_BOT_TOKEN'))


def run_debug():
    log.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--wait', action='store_true', default=False)
    args = parser.parse_args()

    log.debug(f'debug args: {args}')

    import ptvsd
    ptvsd.enable_attach()
    if args.wait:
        ptvsd.wait_for_attach()

    bot = MemeBot(known_memes=ALL_MEMES, guild_config=os.getenv('MEME_BOT_TEST_GUILD_CONFIG'))
    bot.run(os.getenv('MEME_BOT_TEST_TOKEN'))

if __name__ == "__main__":
    run()
