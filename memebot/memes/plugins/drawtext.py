import textwrap
from typing import Dict, Tuple
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, Position, AutoPosition, find_centered_position, draw_outlined_text


class DrawText(BasePlugin):
    position: Position = AutoPosition.BOTTOM
    maxwidth: int = 20
    font: str = 'Impact'
    fontsize: int = 48
    hastextoutline: bool = True
    fontcolor: str = 'white'

    async def run(self, image: Image, context: Dict):
        text = textwrap.fill(self.get_input(context), self.maxwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, self.fontsize)

        position = self.get_text_position(image, draw, font, text)

        if self.hastextoutline:
            draw_outlined_text(draw, position, text, font=font, fill=self.fontcolor)
        else:
            draw.multiline_text(position, text, align='center', font=font, fill=self.fontcolor)

    def get_text_position(self, image: Image, draw: ImageDraw, font: ImageFont, text: str) -> Tuple[float, float]:
        center = (image.size[0] / 2, image.size[1] / 2)
        position_centered_x, position_centered_y = find_centered_position(center, draw.textsize(text, font=font))

        if isinstance(self.position, Coordinate):
            return find_centered_position((self.position.x, self.position.y), draw.textsize(text, font=font))
        elif self.position == AutoPosition.TOP:
            position_y = image.size[1] * 0.05
        elif self.position == AutoPosition.CENTER:
            position_y = position_centered_y
        elif self.position == AutoPosition.BOTTOM:
            position_y = (image.size[1] * 0.95) - draw.textsize(text, font=font)[1]

        return (position_centered_x, position_y)
