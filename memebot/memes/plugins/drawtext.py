import textwrap
import attr
from typing import Dict
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, Position, find_centered_position, draw_outlined_text


@attr.s(kw_only=True)
class DrawText(BasePlugin):
    position: Position = attr.ib(default=Position.BOTTOM)
    customposition: Coordinate = attr.ib(default=None)
    maxwidth: int = attr.ib(default=20)
    font: str = attr.ib(default='Impact')
    fontsize: int = attr.ib(default=48)
    hastextoutline: bool = attr.ib(default=True)
    fontcolor: str = attr.ib(default='white')

    async def run(self, image: Image, context: Dict):
        text = textwrap.fill(context[self.inputtextkey], self.maxwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, self.fontsize)

        position = self.gettextposition(image, draw, font, text)

        if self.hastextoutline:
            draw_outlined_text(draw, position, text, font=font, fill=self.fontcolor)
        else:
            draw.multiline_text(position, text, align='center', font=font, fill=self.fontcolor)

    def gettextposition(self, image: Image, draw: ImageDraw, font: ImageFont, text: str) -> (float, float):
        center = (image.size[0] / 2, image.size[1] / 2)
        position_centered_x, position_centered_y = find_centered_position(center, draw.textsize(text, font=font))

        if self.position == Position.CUSTOM and self.customposition is not None:
            #pylint: disable=no-member
            return find_centered_position((self.customposition.x, self.customposition.y), draw.textsize(text, font=font))
        elif self.position == Position.TOP:
            position_y = image.size[1] * 0.05
        elif self.position == Position.CENTER:
            position_y = position_centered_y
        elif self.position == Position.BOTTOM:
            position_y = (image.size[1] * 0.95) - draw.textsize(text, font=font)[1]

        return (position_centered_x, position_y)
