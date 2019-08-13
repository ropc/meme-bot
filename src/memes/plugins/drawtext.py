import textwrap
import attr
from enum import IntEnum
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import find_centered_position, draw_outlined_text


class TextPosition(IntEnum):
    TOP = 1
    CENTER = 2
    BOTTOM = 3
    CUSTOM = 4

@attr.s
class Coordinate:
    x: float = attr.ib()
    y: float = attr.ib()

@attr.s
class DrawText(BasePlugin):
    position: TextPosition = attr.ib(default=TextPosition.BOTTOM)
    customposition: Coordinate = attr.ib(default=None)
    maxwidth: int = attr.ib(default=20)
    font: str = attr.ib(default='Impact')
    fontsize: int = attr.ib(default=48)
    hasborder: bool = attr.ib(default=True)
    fontcolor: str = attr.ib(default='white')

    def draw(self, image: Image, text: str) -> str:
        text = textwrap.fill(text, self.maxwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, self.fontsize)

        position = self.gettextposition(image, draw, font, text)

        if self.hasborder:
            draw_outlined_text(draw, position, text, font=font, fill=self.fontcolor)
        else:
            draw.multiline_text(position, text, align='center', font=font, fill=self.fontcolor)

        return text

    def gettextposition(self, image: Image, draw: ImageDraw, font: ImageFont, text: str) -> (float, float):
        center = (image.size[0] / 2, image.size[1] / 2)
        position_centered_x, position_centered_y = find_centered_position(center, draw.textsize(text, font=font))

        if self.position == TextPosition.CUSTOM and self.customposition:
            return find_centered_position((self.customposition.x, self.customposition.y), draw.textsize(text, font=font))
        elif self.position == TextPosition.TOP:
            position_y = image.size[1] * 0.05
        elif self.position == TextPosition.CENTER:
            position_y = position_centered_y
        elif self.position == TextPosition.BOTTOM:
            position_y = (image.size[1] * 0.95) - draw.textsize(text, font=font)[1]

        return (position_centered_x, position_y)
