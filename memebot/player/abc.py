from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Generic, Tuple, Optional
from uuid import UUID
from .events import PlayerEvent, SearchEvent
from .item import PlaybackItem


class PlayerABC(ABC):
    @abstractmethod
    async def enqueue(self, text: str):
        pass

    @abstractmethod
    async def skip(self):
        pass


class PlayerDelegate(ABC):
    @abstractmethod
    async def player_event(self, player: PlayerABC, event: PlayerEvent):
        pass

    @abstractmethod
    async def search_event(self, player: PlayerABC, event: SearchEvent):
        pass


I = TypeVar('I')
O = TypeVar('O')
class AsyncProviderABC(Generic[I, O]):
    @abstractmethod
    async def provide(self, input: I) -> O:
        pass


PlaybackItemProvider = AsyncProviderABC[Tuple[str, UUID], PlaybackItem]
DownloadUrlProvider = AsyncProviderABC[str, Optional[str]]


class ItemDownloader(ABC):
    class State(Enum):
        DOWNLOADED_SUCCESSFULLY = 1
        ALREADY_DOWNLOADED = 2
        ERROR_DOWNLOADING = 3

        def is_error(self):
            return self == 3

    @abstractmethod
    async def download(self, item: PlaybackItem) -> State:
        """Download video for given url or item

        This call is idempotent per item.filepath
        
        Arguments:
            item {PlaybackItem} -- item to download
        """
        pass
