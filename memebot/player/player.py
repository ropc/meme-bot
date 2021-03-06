import abc
import os
import asyncio
import aiohttp
import collections
import enum
import discord
import time
import youtube_dl as yt
import logging
import uuid
import urllib.parse
import lxml.html
from pydantic import BaseModel
from typing import Dict, Deque, Callable, Awaitable, Union, Optional, TypeVar, Generic, Tuple
from .events import PlayerEvent, SearchEvent
from .item import PlaybackItem
from .abc import PlayerABC, PlayerDelegate, DownloadUrlProvider, PlaybackItemProvider, ItemDownloader
from .youtube import YoutubeUrlProvider, YoutubePlaybackItemProvider, YoutubeItemDownloader

log = logging.getLogger('memebot')


class Player(PlayerABC):

    def __init__(self, *, voice_channel: discord.VoiceChannel, delegate: PlayerDelegate,
        voice_client: Optional[discord.VoiceClient]=None, queue: Deque[PlaybackItem]=None,
        lock: asyncio.Lock=None, loop: asyncio.AbstractEventLoop=None,
        download_url_provider: DownloadUrlProvider=None,
        playback_item_provider: PlaybackItemProvider=None,
        item_downloader: ItemDownloader=None,
        guild_id: int):
        self._voice_channel = voice_channel
        self.delegate = delegate
        self._voice_client: Optional[discord.VoiceClient] = voice_client
        self._playback_queue: Deque[PlaybackItem] = queue or collections.deque()
        self._queue_lock: asyncio.Lock = lock or asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._download_url_provider: DownloadUrlProvider = download_url_provider or YoutubeUrlProvider()
        self._playback_item_provider: PlaybackItemProvider = playback_item_provider or YoutubePlaybackItemProvider()
        self._item_downloader: ItemDownloader = item_downloader or YoutubeItemDownloader()
        self.now_playing_item: Optional[PlaybackItem] = None
        self.guild_id = guild_id

    @property
    def playback_queue(self):
        return self._playback_queue.copy()

    async def enqueue(self, text: str):
        transaction_id = uuid.uuid4()
        async with self._queue_lock:
            url = text if text.startswith('http') else await self._search(text, transaction_id)
            if not url:
                return
            item = await self._playback_item_provider.provide((url, transaction_id))
            self._playback_queue.append(item)

        await self.delegate.player_event(self, PlayerEvent(event_type=PlayerEvent.Type.ENQUEUED, item=item, guild_id=self.guild_id))

        await self._download(item)

        if not self._voice_client or not self._voice_client.is_playing():
            await self._play_next()

    async def skip(self):
        log.debug(f'skipping current song (if any) on {self._voice_channel}')
        # If already playing, calling `VoiceClient.stop()` will trigger after() to be called
        # which will play the next song in the playlist
        # TODO: A better fix might be to keep track of keys/ids for the next song to play
        if self._voice_client and self._voice_client.is_playing():
            self._voice_client.stop()
        else:
            await self._play_next()

    async def remove(self, index: int):
        if index >= 0 and index < len(self._playback_queue):
            del self._playback_queue[index]

    async def _connected_voice_client(self):
        if not self._voice_client or not self._voice_client.is_connected():
            log.debug(f'creating new voice client for {self._voice_channel}')
            self._voice_client = await self._voice_channel.connect()
        return self._voice_client

    async def _play_next(self):
        if len(self._playback_queue) == 0:
            log.debug(f'nothing in queue for voice_channel: {self._voice_channel}')
            return

        item = self._playback_queue.popleft()
        await self._download(item)

        voice_client = await self._connected_voice_client()

        log.info(f'gonna play {item.title} from {item.url}')
        try:
            voice_client.play(discord.FFmpegPCMAudio(item.filepath), after=self._create_after(item))
        except discord.ClientException as e:
            log.warning(f'Error when trying to play {item.title}', exc_info=True)  # this shouldn't happen
            await self.delegate.player_event(self, PlayerEvent(event_type=PlayerEvent.Type.PLAYBACK_ERROR, item=item, guild_id=self.guild_id))
            return

        self.now_playing_item = item
        await self.delegate.player_event(self, PlayerEvent(event_type=PlayerEvent.Type.STARTED, item=item, guild_id=self.guild_id))

    def _create_after(self, item: PlaybackItem):
        async def try_disconnect():
            if len(self._playback_queue) > 0 or self._voice_client is None or self._voice_client.is_playing():
                log.debug(f'no need to disconnect. playback_queue: {self._playback_queue} voice_client: {self._voice_client}')
                return
            log.debug(f'disconnecting voice_client: {self._voice_client} (voice_channel: {self._voice_channel})')
            await self._voice_client.disconnect()
            self._voice_client = None

        async def async_after(error):
            event_type = PlayerEvent.Type.PLAYBACK_ERROR if error else PlayerEvent.Type.FINISHED
            was_last_item = len(self._playback_queue) == 0
            log.debug(f'finished playback. event_type: {event_type} was_last_item: {was_last_item}')
            await asyncio.gather(
                self.delegate.player_event(self, PlayerEvent(event_type=event_type, item=item, guild_id=self.guild_id)),
                self._play_next()
            )
            # technically, this could be replayed. either now or in the future.
            if os.path.isfile(item.filepath):
                os.remove(item.filepath)
            if was_last_item:
                await asyncio.sleep(5 * 60)
                await try_disconnect()

        def after(error):
            self._now_playing_item = None  # don't want any delay for this
            self._loop.create_task(async_after(error))

        return after

    async def _download(self, item: PlaybackItem):
        state = await self._item_downloader.download(item)
        if state.is_error():
            self.delegate.player_event(self, PlayerEvent(event_type=PlayerEvent.Type.DOWNLOAD_ERROR, item=item, guild_id=self.guild_id))

    async def _search(self, keyword: str, transaction_id: uuid.UUID) -> Optional[str]:
        '''Searches for keyword and emits `SearchEvent`s'''
        result, _ = await asyncio.gather(
            self._download_url_provider.provide(keyword),
            self.delegate.search_event(self, SearchEvent(event_type=SearchEvent.Type.SEARCHING, keyword=keyword, transaction_id=transaction_id, guild_id=self.guild_id))
        )

        if not result:
            await self.delegate.search_event(self, SearchEvent(event_type=SearchEvent.Type.SEARCH_ERROR, keyword=keyword, transaction_id=transaction_id, guild_id=self.guild_id))
            return None

        return result
