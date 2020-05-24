import textwrap
import enum
from typing import Dict, Tuple
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, Position, AutoPosition, find_centered_position


class TextStyle(enum.Enum):
    WHITE = 1
    BLACK = 2


class DrawText(BasePlugin):
    position: Position = AutoPosition.BOTTOM
    maxwidth: int = 20
    fontsize: int = 48
    textstyle: TextStyle = TextStyle.WHITE

    async def run(self, image: Image, context: Dict):
        text = textwrap.fill(self.get_input(context), self.maxwidth)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('Impact', self.fontsize)

        position = self.get_text_position(image, draw, font, text)

        if self.textstyle == TextStyle.WHITE:
            draw_outlined_text(draw, position, text, font=font, fill='white')
        else:
            draw.multiline_text(position, text, align='center', font=font, fill='black')

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


def draw_outlined_text(draw: ImageDraw, position, text: str, **kwargs):
    x, y = position
    shadowcolor = 'black'
    nonfill_kargs = {k:v for (k, v) in kwargs.items() if k != 'fill'}  # gross
    draw.multiline_text((x-1, y-1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y-1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x-1, y+1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y+1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text(position, text, align='center', spacing=4, **kwargs)
