import attr
from PIL import Image
from .baseplugin import BasePlugin


@attr.s
class OverrideText(BasePlugin):
    text: str = attr.ib()

    def draw(self, image: Image, text: str) -> str:
        return self.text