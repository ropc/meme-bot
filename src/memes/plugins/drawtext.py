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

@attr.s
class DrawText(BasePlugin):
    position: TextPosition = attr.ib(default=TextPosition.BOTTOM)
    hasborder: bool = attr.ib(default=True)
    maxwidth: int = attr.ib(default=20)
    font: str = attr.ib(default='Impact')
    fontsize: int = attr.ib(default=48)

    def draw(self, image: Image, text: str) -> str:
        text = textwrap.fill(text, self.maxwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, self.fontsize)

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