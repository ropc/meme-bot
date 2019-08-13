import abc
import attr
from typing import List
from PIL import Image
from .basememe import BaseMeme
from .plugins import BasePlugin


@attr.s
class MemeConfig:
    image_filename: str = attr.ib()
    plugins: List[BasePlugin] = attr.ib()


class GenericMeme(BaseMeme):

    def __init__(self, config: MemeConfig):
        self.config = config

    def image_filename(self):
        return self.config.image_filename

    def draw_meme(self, image: Image, text: str):
        for plugin in self.config.plugins:
            text = plugin.draw(image, text)
