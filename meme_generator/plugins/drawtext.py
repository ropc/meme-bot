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

    async def run(self, image: Image.Image, text: str, context: Dict):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('Impact', self.fontsize)
        text = textwrap.fill(text, self.maxwidth)

        textbox = draw.multiline_textbbox((0,0), text, font=font)
        width = textbox[2]
        height = textbox[3]

        if self.position == AutoPosition.TOP:
            drawposition = ((image.size[0] / 2) - (width / 2), image.size[1] * 0.05)
        elif self.position == AutoPosition.CENTER:
            drawposition = ((image.size[0] / 2) - (width / 2), (image.size[1] * 0.5) - (height / 2))
        elif self.position == AutoPosition.BOTTOM:
            drawposition = ((image.size[0] / 2) - (width / 2), (image.size[1] * 0.95) - height)
        elif isinstance(self.position, Coordinate):
            drawposition = (self.position.x - (width / 2), self.position.y - (height / 2))

        if self.textstyle == TextStyle.WHITE:
            draw_outlined_text(draw, drawposition, text, font=font)
        else:
            draw.multiline_text(drawposition, text, fill='black', align='center', spacing=4, font=font)


def draw_outlined_text(draw: ImageDraw.ImageDraw, position, text: str, **kwargs):
    x, y = position
    nonfill_kargs = {k:v for (k, v) in kwargs.items() if k != 'fill'}  # gross
    draw.multiline_text((x-1, y-1), text, fill='black', align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y-1), text, fill='black', align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x-1, y+1), text, fill='black', align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y+1), text, fill='black', align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text(position, text, fill='white', align='center', spacing=4, **kwargs)

