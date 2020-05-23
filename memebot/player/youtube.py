import asyncio
import logging
import os
import urllib
import aiohttp
import lxml
import youtube_dl as yt
from typing import Optional, Tuple
from uuid import UUID
from .abc import PlaybackItemProvider, DownloadUrlProvider, ItemDownloader
from .item import PlaybackItem

log = logging.getLogger('memebot')

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

yt_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '/tmp/%(id)s.%(ext)s'
}


class YoutubeUrlProvider(DownloadUrlProvider):
    async def provide(self, keyword: str) -> Optional[str]:
        return await _find_url_scrape(keyword) or await _find_url_api(keyword)


class YoutubePlaybackItemProvider(PlaybackItemProvider):
    async def provide(self, input: Tuple[str, UUID]) -> PlaybackItem:
        url, transaction_id = input
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


class YoutubeItemDownloader(ItemDownloader):
    async def download(self, item: PlaybackItem) -> ItemDownloader.State:
        def download_notify_error(ytdl) -> ItemDownloader.State:
            try:
                ytdl.download([item.url])
                return ItemDownloader.State.DOWNLOADED_SUCCESSFULLY
            except KeyboardInterrupt:
                raise
            except:
                return ItemDownloader.State.ERROR_DOWNLOADING

        if os.path.isfile(item.filepath):
            log.debug(f'already downloaded {item.filepath}')
            return ItemDownloader.State.ALREADY_DOWNLOADED

        with yt.YoutubeDL(yt_opts) as ytdl:
            # need to run_in_executor to prevent blocking
            return await asyncio.get_event_loop().run_in_executor(None, download_notify_error, ytdl)


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
