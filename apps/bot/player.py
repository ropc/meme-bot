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
from pydantic import BaseModel
from typing import Dict, Deque, Callable, Awaitable, Union, Optional


log = logging.getLogger('memebot')

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

yt_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '/tmp/%(id)s.%(ext)s'
}


class PlaybackItem(BaseModel):
    title: str
    url: str
    filepath: str
    download_url: str


class PlayerEventType(enum.Enum):
    ENQUEUED = 1
    STARTED = 2
    FINISHED = 3
    PLAYBACK_ERROR = 4


class PlayerEvent(BaseModel):
    event_type: PlayerEventType
    context: PlaybackItem


class SearchEventType(enum.Enum):
    SEARCHING = 1
    SEARCH_ERROR = 2


class SearchEvent(BaseModel):
    event_type: SearchEventType
    keyword: str


PlayerEventCallback = Callable[[Union[PlayerEvent, SearchEvent]], Awaitable[None]]


class Player:

    def __init__(self, voice_client: discord.VoiceClient, on_event_cb: PlayerEventCallback):
        self.voice_client = voice_client
        self.on_event_cb = on_event_cb
        self.playback_queue: Deque[PlaybackItem] = collections.deque()
        self.download_lock = asyncio.Lock()
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    async def enqueue(self, text: str):
        async with self.download_lock:
            url = text if text.startswith('http') else await self._search(text)
            if not url:
                await self.on_event_cb(SearchEvent(event_type=SearchEventType.SEARCH_ERROR, keyword=text))
                return
            item = await self._get_item(url)
            self.playback_queue.append(item)

        await asyncio.gather(
            self.on_event_cb(PlayerEvent(event_type=PlayerEventType.ENQUEUED, context=item)),
            self._download(item)
        )

        if not self.voice_client.is_playing():
            await self._play_next()

    async def skip(self):
        self.voice_client.stop()
        await self._play_next()

    async def _play_next(self):
        if len(self.playback_queue) == 0:
            return
        item = self.playback_queue.popleft()
        await self._download(item)
        log.info(f"gonna play {item.url}")
        self.voice_client.play(discord.FFmpegPCMAudio(item.filepath), after=self._create_after(item))
        await self.on_event_cb(PlayerEvent(event_type=PlayerEventType.STARTED, context=item))
    
    def _create_after(self, item: PlaybackItem):
        async def after(error):
            event_type = PlayerEventType.PLAYBACK_ERROR if error else PlayerEventType.FINISHED
            await asyncio.gather(
                self.on_event_cb(PlayerEvent(event_type=event_type, context=item)),
                self._play_next()
            )
            if os.path.isfile(item.filepath):
                os.remove(item.filepath)
        return lambda error: self.loop.create_task(after(error))

    async def _get_item(self, url: str) -> PlaybackItem:
        with yt.YoutubeDL(yt_opts) as ytdl:
            info = ytdl.extract_info(url, download=False)
            filepath = ytdl.prepare_filename(info)
            log.debug(f'info for {url}: {info}')
            return PlaybackItem(title=info['title'], url=url, filepath=filepath, download_url=info['url'])

    async def _download(self, item: PlaybackItem):
        """Download video for given url or item

        This call is idempotent per item.filepath
        
        Arguments:
            item {PlaybackItem} -- item to download
        """
        if os.path.isfile(item.filepath):
            log.info(f'already downloaded {item.filepath}')
            return
        with yt.YoutubeDL(yt_opts) as ytdl:
            ytdl.download([item.url])


    async def _search(self, keyword: str) -> Optional[str]:
        result = await asyncio.gather(
            _find_url(keyword),
            self.on_event_cb(SearchEvent(event_type=SearchEventType.SEARCHING, keyword=keyword))
        )
        return result[0]


async def _find_url(keyword: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:  # type: aiohttp.ClientSession
        params = {
            'part': 'id',
            'key': os.getenv('MEME_BOT_GOOGLE_API_KEY'),
            'q': keyword,
            'maxResults': 1,
            'type': 'video'
        }
        async with session.get(YOUTUBE_SEARCH_URL, params=params) as response:  # type: aiohttp.ClientResponse
            content = await response.json()
            videoId = content.get('items', [{}])[0].get('id', {}).get('videoId')
            if not videoId:
                return None
            return f'https://www.youtube.com/watch?v={videoId}'
