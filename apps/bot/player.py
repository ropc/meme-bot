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
    transaction_id: uuid.UUID
    filepath: str
    download_url: str


class PlayerEventType(enum.Enum):
    ENQUEUED = 1
    STARTED = 2
    FINISHED = 3
    PLAYBACK_ERROR = 4
    DOWNLOAD_ERROR = 5


class PlayerEvent(BaseModel):
    event_type: PlayerEventType
    item: PlaybackItem

    @property
    def transaction_id(self) -> uuid.UUID:
        return self.item.transaction_id


# TODO: Figure out how to merge this into PlayerEventType
class SearchEventType(enum.Enum):
    SEARCHING = 1
    SEARCH_ERROR = 3


class SearchEvent(BaseModel):
    event_type: SearchEventType
    keyword: str
    transaction_id: uuid.UUID


class PlayerDelegate(abc.ABC):
    @abc.abstractmethod
    async def player_event(self, player: 'Player', event: PlayerEvent):
        pass
    @abc.abstractmethod
    async def search_event(self, player: 'Player', event: SearchEvent):
        pass


class Player:

    def __init__(self, voice_channel: discord.VoiceChannel, delegate: PlayerDelegate):
        self.voice_channel = voice_channel
        self.delegate = delegate
        self.voice_client: Optional[discord.VoiceClient] = None
        self.playback_queue: Deque[PlaybackItem] = collections.deque()
        self.queue_lock = asyncio.Lock()
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    async def enqueue(self, text: str):
        transaction_id = uuid.uuid4()
        async with self.queue_lock:
            url = text if text.startswith('http') else await self._search(text, transaction_id)
            if not url:
                return
            item = await self._get_item(url, transaction_id)
            self.playback_queue.append(item)

        await self.delegate.player_event(self, PlayerEvent(event_type=PlayerEventType.ENQUEUED, item=item))

        await self._download(item)

        if not self.voice_client or not self.voice_client.is_playing():
            await self._play_next()

    async def skip(self):
        log.debug(f'skipping current song (if any) on {self.voice_channel}')
        self.voice_client.stop()
        await self._play_next()

    async def _connected_voice_client(self):
        if not self.voice_client or not self.voice_client.is_connected():
            log.debug(f'creating new voice client for {self.voice_channel}')
            self.voice_client = await self.voice_channel.connect()
        return self.voice_client

    async def _play_next(self):
        if len(self.playback_queue) == 0:
            log.debug(f'nothing in queue for voice_channel: {self.voice_channel}')
            return

        item = self.playback_queue.popleft()
        await self._download(item)

        voice_client = await self._connected_voice_client()

        log.info(f'gonna play {item.title} from {item.url}')
        voice_client.play(discord.FFmpegPCMAudio(item.filepath), after=self._create_after(item))
        await self.delegate.player_event(self, PlayerEvent(event_type=PlayerEventType.STARTED, item=item))
    
    def _create_after(self, item: PlaybackItem):
        async def try_disconnect():
            if len(self.playback_queue) > 0 or self.voice_client is None or self.voice_client.is_playing():
                log.debug(f'no need to disconnect. playback_queue: {self.playback_queue} voice_client: {self.voice_client}')
                return
            log.debug(f'disconnecting voice_client: {self.voice_client} (voice_channel: {self.voice_channel})')
            await self.voice_client.disconnect()
            self.voice_client = None

        async def after(error):
            event_type = PlayerEventType.PLAYBACK_ERROR if error else PlayerEventType.FINISHED
            was_last_item = len(self.playback_queue) == 0
            log.debug(f'finished playback. event_type: {event_type} was_last_item: {was_last_item}')
            await asyncio.gather(
                self.delegate.player_event(self, PlayerEvent(event_type=event_type, item=item)),
                self._play_next()
            )
            # technically, this could be replayed. either now or in the future.
            if os.path.isfile(item.filepath):
                os.remove(item.filepath)
            if was_last_item:
                await asyncio.sleep(5 * 60)
                await try_disconnect()

        return lambda error: self.loop.create_task(after(error))

    async def _get_item(self, url: str, transaction_id: uuid.UUID) -> PlaybackItem:
        with yt.YoutubeDL(yt_opts) as ytdl:
            info = ytdl.extract_info(url, download=False)
            filepath = ytdl.prepare_filename(info)
            log.debug(f'got info for {url}')
            return PlaybackItem(
                title=info['title'],
                url=url,
                filepath=filepath,
                download_url=info['url'],
                transaction_id=transaction_id)

    async def _download(self, item: PlaybackItem):
        """Download video for given url or item

        This call is idempotent per item.filepath
        
        Arguments:
            item {PlaybackItem} -- item to download
        """
        def download_notify_error(ytdl):
            try:
                ytdl.download([item.url])
            except KeyboardInterrupt:
                raise
            except:
                self.delegate.player_event(self, PlayerEvent(event_type=PlayerEventType.DOWNLOAD_ERROR, item=item))

        if os.path.isfile(item.filepath):
            log.debug(f'already downloaded {item.filepath}')
            return

        with yt.YoutubeDL(yt_opts) as ytdl:
            # need to run_in_executor to prevent blocking
            await self.loop.run_in_executor(None, download_notify_error, ytdl)


    async def _search(self, keyword: str, transaction_id: uuid.UUID) -> Optional[str]:
        '''Searches for keyword and emits `SearchEvent`s'''
        result, _ = await asyncio.gather(
            _find_url(keyword),
            self.delegate.search_event(self, SearchEvent(event_type=SearchEventType.SEARCHING, keyword=keyword, transaction_id=transaction_id))
        )

        if not result:
            await self.delegate.search_event(self, SearchEvent(event_type=SearchEventType.SEARCH_ERROR, keyword=keyword, transaction_id=transaction_id))
            return None

        return result


async def _find_url_scrape(keyword: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:  # type: aiohttp.ClientSession
        log.debug(f'scraping youtube with keyword: {keyword}')
        async with session.get(f'https://www.youtube.com/results?search_query={keyword}') as response:  # type: aiohttp.ClientResponse
            html = lxml.html.fromstring(await response.text())
            link_attributes = (e.attrib for e in html.xpath("//*[contains(@class, 'yt-uix-tile-link')]"))
            for attributes in link_attributes:
                href = attributes.get('href', '')
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                if len(query_params) != 1 or len(query_params.get('v', [])) != 1:
                    continue
                url = f"https://www.youtube.com/watch?v={query_params['v'][0]}"
                log.debug(f'scrape youtube link for query "{keyword}": {url}')
                return url
    return None


async def _find_url_api(keyword: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:  # type: aiohttp.ClientSession
        params = {
            'part': 'id',
            'key': os.getenv('MEME_BOT_GOOGLE_API_KEY'),
            'q': keyword,
            'maxResults': 1,
            'type': 'video'
        }
        log.debug(f'querying youtube api with keyword: {keyword}')
        async with session.get(YOUTUBE_SEARCH_URL, params=params) as response:  # type: aiohttp.ClientResponse
            content = await response.json()
            videoId = content.get('items', [{}])[0].get('id', {}).get('videoId')
            if not videoId:
                log.warning(f'did not find videoId for query "{keyword}"')
                return None
            url = f'https://www.youtube.com/watch?v={videoId}'
            log.debug(f'api youtube link for query "{keyword}": {url}')
            return url


async def _find_url(keyword: str) -> Optional[str]:
    return await _find_url_scrape(keyword) or await _find_url_api(keyword)
