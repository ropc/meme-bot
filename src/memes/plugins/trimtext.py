import attr
from PIL import Image
from .baseplugin import BasePlugin


@attr.s
class TrimText(BasePlugin):
    numwords: int = attr.ib()

    def draw(self, image: Image, text: str) -> str:
        return ''.join(text.split(' ')[:self.numwords])
