import os
import random
import logging
import discord
from pydantic import BaseModel
from pygtrie import CharTrie
from typing import Dict, List, Callable, Awaitable, Optional, MutableMapping, Tuple, Union
from ..meme_generator import Meme, ALL_MEMES
from .command import Command, CommandExecutor
from .player import Player, PlayerEvent, PlayerEventType, SearchEvent

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

    def __init__(self, *, known_memes: List[Meme]):
        super().__init__()
        self.guild_player_config: MutableMapping[int, PlayerConfig] = {}

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

        # player commands
        self.commands['!play'] = create_play_executor(self.guild_player_config.get)
        self.commands['!skip'] = create_skip_executor(self.guild_player_config.get)
        self.commands['!queue'] = create_show_queue_executor(self.guild_player_config.get)

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
        log.debug('setting up voice channels')
        # TODO: handle reconnects
        # TODO: handle multiple guilds
        guild_id = os.getenv('TEST_GUILD_ID')
        guild_ids = [g.id for g in self.guilds]
        if guild_id not in guild_ids:
            log.info(f'guild not found in {guild_ids}')
            return
        voice_channel_id = os.getenv('TEST_VOICE_ID')
        text_channel_id = os.getenv('TEST_TEXT_ID')
        voice_channel: discord.VoiceChannel = self.get_channel(voice_channel_id)
        text_channel: discord.TextChannel = self.get_channel(text_channel_id)

        if not voice_channel or not text_channel:
            log.warning(f'could not get defined voice/text channels')
            return

        log.info(f'connecting to voice channel: {voice_channel.name}')
        voice_client: discord.VoiceClient = await voice_channel.connect()

        player = Player(voice_client=voice_client, on_event_cb=create_player_event_handler(text_channel))

        self.guild_player_config[guild_id] = PlayerConfig(player=player, voice_channel_id=voice_channel_id, text_channel_id=text_channel_id)

        log.debug('done setting up voice channels')


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
    def wrapper(func: PlayerCommandExecutor):
        def wrapped(command_arg: str, channel: discord.TextChannel):
            config = player_config_provider(channel.guild.id)
            if not config:
                log.debug(f'could not find config for guild id {channel.guild.id}')
                return
            if config.text_channel_id != channel.id:
                log.debug(f'player command in guild {channel.guild.id} did not come from PlayerConfig.text_channel_id {config.text_channel_id}')
                return
            return func(command_arg, channel, config)
        return wrapped
    return wrapper


def create_play_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def play(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        await player_config.player.enqueue(command_arg)
    return play


def create_skip_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def skip(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        await player_config.player.skip()
    return skip


def create_show_queue_executor(player_config_provider: PlayerConfigProvider) -> CommandExecutor:
    @ignore_by_player_config_provider(player_config_provider)
    async def show_queue(command_arg: str, channel: discord.TextChannel, player_config: PlayerConfig):
        queue = '\n'.join(f'- {item.title}' for item in player_config.player.playback_queue)
        await channel.send(f'Up next:\n{queue}')
    return show_queue


def create_player_event_handler(text_channel: discord.TextChannel):
    async def player_event_handler(event: PlayerEvent):
        if event.event_type == PlayerEventType.ENQUEUED:
            await text_channel.send(f'Enqueued: {event.context.title}', delete_after=60)
        elif event.event_type == PlayerEventType.STARTED:
            await text_channel.send(f'Now playing: {event.context.title}')

    async def search_event_handler(event: SearchEvent):
        await text_channel.send(f'Searching for "{event.keyword}"')

    async def handler(event: Union[PlayerEvent, SearchEvent]):
        log.debug(f'player handler received event: {event}')
        if isinstance(event, PlayerEvent):
            await player_event_handler(event)
        else:
            await search_event_handler(event)
    return handler


def create_meme_executor(meme_generator: Meme) -> CommandExecutor:
    async def run_meme(command_arg: str, channel: discord.abc.Messageable):
        async with meme_generator.generate(command_arg) as meme_image:
            df = discord.File(meme_image, filename=meme_generator.image_filename)
            return await channel.send(file=df)
    return run_meme


def create_text_response_executor(text: str) -> CommandExecutor:
    async def send_text(command_arg: str, channel: discord.abc.Messageable):
        return await channel.send(text)
    return send_text


async def roll_dice(command_arg: str, channel: discord.abc.Messageable):
    num_dice, num_sides = [int(x if x else 1) for x in command_arg.split('d')]

    # soft limit. (2k - 16) hardcoded characters in message
    if num_dice * num_sides.bit_length() > 1984:
        return await channel.send("I don't have all those dice")

    raw_rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(raw_rolls)

    if len(raw_rolls) > 1:
        formatted_rolls = ', '.join(str(r) for r in raw_rolls)
        message = f'Total: {total}, rolls: {formatted_rolls}'
    else:
        message = f'Total: {total}'

    if len(message) > 2000:  # discord has a 2k message limit
        return await channel.send("I don't have all those dice")

    return await channel.send(message)


def run():
    bot = MemeBot(known_memes=ALL_MEMES)
    bot.run(os.getenv('MEME_BOT_TOKEN'))


def run_debug():
    log.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    import ptvsd
    ptvsd.enable_attach()

    bot = MemeBot(known_memes=ALL_MEMES)
    bot.run(os.getenv('MEME_BOT_TEST_TOKEN'))

if __name__ == "__main__":
    run()
