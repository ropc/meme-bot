import pytest
from uuid import uuid4
from discord import VoiceChannel
from unittest.mock import patch, Mock, AsyncMock
from memebot.player import Player, PlayerDelegate, PlayerABC, PlayerEvent, SearchEvent, PlaybackItem
from memebot.player.abc import DownloadUrlProvider, PlaybackItemProvider, ItemDownloader


@pytest.fixture
def player():
    player_delegate = Mock(PlayerDelegate)
    voice_channel = Mock(VoiceChannel)
    url_provider = Mock(DownloadUrlProvider)
    url_provider.provide = AsyncMock()
    url_provider.provide.return_value = 'url'
    item_downloader = Mock(ItemDownloader)
    item_downloader.download = AsyncMock()
    item_downloader.download.return_value = ItemDownloader.State.DOWNLOADED_SUCCESSFULLY
    playback_item_provider = Mock(PlaybackItemProvider)
    playback_item_provider.provide = AsyncMock()
    playback_item_provider.provide.return_value = PlaybackItem(title='', url='', transaction_id=uuid4(), filepath='', download_url='')
    return Player(
        voice_channel=voice_channel,
        delegate=player_delegate,
        download_url_provider=url_provider,
        playback_item_provider=playback_item_provider,
        item_downloader=item_downloader)

def test_cannot_directly_modify_queue(player: Player):
    assert len(player.playback_queue) == 0
    player.playback_queue.append(1)
    assert len(player.playback_queue) == 0

@pytest.mark.asyncio
async def test_fast_enqueue(player: Player):
    await player.enqueue("rhcp snow")
    assert len(player.playback_queue) == 1
