import abc
import asyncio
import logging
import uuid
import discord
from discord.ext import commands
from pydantic import BaseModel
from typing import Optional, Callable, Dict
from memebot.guildconfig import GuildConfig
from memebot.player import Player, PlayerABC, PlayerDelegate, PlayerEvent, SearchEvent
from memebot.error import MemeBotCheckError


log = logging.getLogger('memebot')


class PlayerConfig(BaseModel):
    player: Player
    voice_channel: discord.VoiceChannel
    text_channel: discord.TextChannel

    class Config:
        arbitrary_types_allowed = True


async def display_queue(context: commands.Context, config: PlayerConfig):
    if len(config.player.playback_queue) == 0:
        return await context.send('Nothing in queue. Add a song with !play', delete_after=30)
    queue = '\n'.join(f'[{idx}] {item.title}' for idx,item in enumerate(config.player.playback_queue))
    return await context.send(f'Up next:\n{queue}', delete_after=60)


def has_player_config(*, voice_restricted=False):
    async def predicate(context: commands.Context):
        if not isinstance(context.cog, CogPlayerConfigChecker):
            return False
        return context.cog.verify_config(context, voice_restricted=voice_restricted)
    return commands.check(predicate)


class CogPlayerConfigChecker(abc.ABC):
    @abc.abstractmethod
    def verify_config(self, context: commands.Context, *, voice_restricted=False):
        pass


class PlayerCogMeta(commands.CogMeta, abc.ABCMeta):
    pass


class PlayerCog(commands.Cog, PlayerDelegate, CogPlayerConfigChecker, metaclass=PlayerCogMeta):

    def __init__(self, bot: commands.Bot, guild_configs: Dict[int, GuildConfig]):
        super().__init__()
        self.bot = bot
        self.guild_configs = guild_configs
        self.guild_player_config: Dict[int, PlayerConfig] = {}
        self.known_messages: Dict[uuid.UUID, discord.Message] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # setup players
        log.info('setting up voice channels')
        for (guild_id, config) in self.guild_configs.items():
            if guild_id in self.guild_player_config:
                log.warning(f'already have player config for guild {guild_id}')
                continue

            voice_channel: discord.VoiceChannel = self.bot.get_channel(config.voice_channel_id)
            text_channel: discord.TextChannel = self.bot.get_channel(config.text_channel_id)

            if not voice_channel or not text_channel:
                log.warning(f'could not get voice/text channels for guild {guild_id}. GuildConfig: {config}')
                continue

            log.debug(f'creating player for voice_channel: {voice_channel} text_channel: {text_channel}')
            player = Player(voice_channel=voice_channel, delegate=self, guild_id=guild_id)

            self.guild_player_config[guild_id] = PlayerConfig(
                player=player,
                voice_channel=voice_channel,
                text_channel=text_channel)

        log.info('done setting up voice channels')

    @commands.command()
    @commands.guild_only()
    @has_player_config(voice_restricted=True)
    async def play(self, context: commands.Context, *, arg: str):
        '''Search for a song and add to queue'''
        config = self._get_config(context)
        await config.player.enqueue(arg)

    @commands.command()
    @commands.guild_only()
    @has_player_config(voice_restricted=True)
    async def skip(self, context: commands.Context):
        '''Skips current song, if one is playing'''
        config = self._get_config(context)
        await asyncio.gather(
            config.player.skip(),
            context.send('Skipping...', delete_after=60)
        )

    @commands.command()
    @commands.guild_only()
    @has_player_config()
    async def queue(self, context: commands.Context):
        '''Shows current queue'''
        config = self._get_config(context)
        await display_queue(context.channel, config)

    @commands.command()
    @commands.guild_only()
    @has_player_config()
    async def remove(self, context: commands.Context, number: int):
        """Allows the removal of a specific song from the queue by index. Usage: !remove 2"""
        config = self._get_config(context)
        await config.player.remove(number)
        await display_queue(context, config)

    @commands.command(aliases=['now playing', 'np'])
    @commands.guild_only()
    @has_player_config()
    async def now_playing(self, context: commands.Context):
        '''Shows song currently playing'''
        config = self._get_config(context)
        if not config.player.now_playing_item:
            await context.send('Nothing playing. Add a song with !play', delete_after=30)
            return
        title = config.player.now_playing_item.title
        await context.send(f'Now playing: {title}', delete_after=60)

    # Player Delegate methods

    async def player_event(self, player: PlayerABC, event: PlayerEvent):
        config = self.guild_player_config.get(event.guild_id)
        if not config:
            return
        log.debug(f'received player event {event} from {player}')
        message = None
        if event.event_type == PlayerEvent.Type.ENQUEUED:
            message = await config.text_channel.send(f'Added to queue: {event.item.title}')
        elif event.event_type == PlayerEvent.Type.STARTED:
            await config.text_channel.send(f'Now playing: {event.item.title}')
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=event.item.title))
        elif event.event_type == PlayerEvent.Type.PLAYBACK_ERROR:
            await config.text_channel.send(f'error when trying to play {event.item.title} =(')
            await self.bot.change_presence()
        elif event.event_type == PlayerEvent.Type.DOWNLOAD_ERROR:
            await config.text_channel.send(f'error when trying to download {event.item.title} =(')
        elif event.event_type == PlayerEvent.Type.FINISHED:
            await self.bot.change_presence()

        await self._delete_previous_and_cache(event.transaction_id, message)

    async def search_event(self, player: PlayerABC, event: SearchEvent):
        config = self.guild_player_config.get(event.guild_id)
        if not config:
            return
        log.debug(f'received search event {event} from {player}')
        message = None
        if event.event_type == SearchEvent.Type.SEARCHING:
            message = await config.text_channel.send(f'Searching for "{event.keyword}"')
        elif event.event_type == SearchEvent.Type.SEARCH_ERROR:
            await config.text_channel.send(f'Could not find "{event.keyword}"')

        await self._delete_previous_and_cache(event.transaction_id, message)

    async def _delete_previous_and_cache(self, transaction_id: uuid.UUID, message: Optional[discord.Message]):
        old_message = self.known_messages.pop(transaction_id, None)
        if old_message:
            await old_message.delete(delay=0)
        if message:
            self.known_messages[transaction_id] = message

    def _get_config(self, context: commands.Context):
        return self.guild_player_config.get(context.guild.id)

    # CogPlayerConfigChecker

    def verify_config(self, context: commands.Context, *, voice_restricted=False):
        config = self._get_config(context)
        if not config:
            log.debug(f'could not find config for guild id {context.guild.id}')
            raise MemeBotCheckError('Player not configured for this server')
        if config.text_channel.id != context.channel.id:
            log.debug(f'player command in guild {context.guild.id} did not come from PlayerConfig.text_channel_id {config.text_channel.id}')
            raise MemeBotCheckError(f'Command must be used in #{config.text_channel.name}')
        if voice_restricted and context.author.id not in (member.id for member in config.voice_channel.members):
            log.debug(f'user {context.author.id} not in voice channel {config.voice_channel.id} for guild {context.guild.id}')
            raise MemeBotCheckError(f'User must be in voice channel {config.voice_channel.name!r} to use this command')
        return True
