from enum import Enum
from uuid import UUID
from pydantic import BaseModel
from .item import PlaybackItem


# class PlayerEventType(Enum):
#     ENQUEUED = 1
#     STARTED = 2
#     FINISHED = 3
#     PLAYBACK_ERROR = 4
#     DOWNLOAD_ERROR = 5


class PlayerEvent(BaseModel):
    class Type(Enum):
        ENQUEUED = 1
        STARTED = 2
        FINISHED = 3
        PLAYBACK_ERROR = 4
        DOWNLOAD_ERROR = 5

    event_type: Type
    item: PlaybackItem
    guild_id: int

    @property
    def transaction_id(self) -> UUID:
        return self.item.transaction_id


# TODO: Figure out how to merge this into PlayerEventType
# class SearchEventType(Enum):
#     SEARCHING = 1
#     SEARCH_ERROR = 3


class SearchEvent(BaseModel):
    class Type(Enum):
        SEARCHING = 1
        SEARCH_ERROR = 3

    event_type: Type
    keyword: str
    transaction_id: UUID
    guild_id: int
