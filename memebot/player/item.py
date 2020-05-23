from uuid import UUID
from pydantic import BaseModel


class PlaybackItem(BaseModel):
    title: str
    url: str
    transaction_id: UUID
    filepath: str
    download_url: str
