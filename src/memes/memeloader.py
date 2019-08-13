from typing import List
from .basememe import BaseMeme
from .genericmeme import GenericMeme, MemeConfig


class MemeLoader:
    def __init__(self, memes: List[MemeConfig]):
        self.dict = {memeconfig.alias: GenericMeme(memeconfig) for memeconfig in memes}

    def get(self, alias: str) -> BaseMeme:
        return self.dict.get(alias)
