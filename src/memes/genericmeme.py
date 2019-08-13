import abc
import enum
import textwrap
import attr
from typing import List
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .basememe import BaseMeme
from .utils import find_centered_position, draw_outlined_text


class TextPosition(enum.IntEnum):
    TOP = 1
    CENTER = 2
    BOTTOM = 3

class Plugin(abc.ABC):
    @abc.abstractmethod
    def draw(self, image: Image, text: str) -> str:
        raise NotImplementedError()

@attr.s
class Text(Plugin):
    position: TextPosition = attr.ib(default=TextPosition.BOTTOM)
    hasborder: bool = attr.ib(default=True)
    maxtextwidth: int = attr.ib(default=20)

    def draw(self, image: Image, text: str) -> str:
        text = textwrap.fill(text, self.maxtextwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('Impact', 48)

        center = (image.size[0] / 2, image.size[1] / 2)
        position_centered_x, position_centered_y = find_centered_position((0, 0), center, draw.textsize(text, font=font))

        if self.position == TextPosition.TOP:
            position_y = image.size[1] * 0.05
        elif self.position == TextPosition.CENTER:
            position_y = position_centered_y
        elif self.position == TextPosition.BOTTOM:
            position_y = (image.size[1] * 0.95) - draw.textsize(text, font=font)[1]

        position = (position_centered_x, position_y)

        if self.hasborder:
            draw_outlined_text(draw, position, font, text)
        else:
            draw.multiline_text(position, text, font=font)

        return text


@attr.s
class SpongifyText(Plugin):
    def draw(self, image: Image, text: str) -> str:
        vowels = set('aoeuiAOEUI')
        return ''.join(letter.lower() if letter in vowels else letter.upper() for letter in text)

@attr.s
class MemeConfig:
    image_filename: str = attr.ib()
    plugins: List[Plugin] = attr.ib()

class Handler(abc.ABC):
    @abc.abstractmethod
    def draw(self, image: Image, text: str) -> str:
        raise NotImplementedError()

class GenericMeme(BaseMeme):

    def __init__(self, config: MemeConfig):
        self.config = config

    def image_filename(self):
        return self.config.image_filename

    def draw_meme(self, image: Image, text: str):
        for plugin in self.config.plugins:
            text = plugin.draw(image, text)
