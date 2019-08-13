from typing import Iterable
from .basememe import BaseMeme
from .genericmeme import GenericMeme, MemeConfig


class MemeLoader:
    def __init__(self, memes: Iterable[MemeConfig]):
        self.dict = {memeconfig.alias: GenericMeme(memeconfig) for memeconfig in memes}

    def get(self, alias: str) -> BaseMeme:
        return self.dict.get(alias)

    def aliases(self) -> Iterable[str]:
        return self.dict.keys()

    def items(self):
        return self.dict.items()
