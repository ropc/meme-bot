import textwrap
import enum
from typing import Dict, Tuple, Optional
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .drawtext import DrawText, TextStyle
from .drawimage import DrawImage
from .utils import Coordinate, Position, AutoPosition


class DrawInput(BasePlugin):
    position: Coordinate
    maxwidth: int = 20
    fontsize: int = 48
    textstyle: TextStyle = TextStyle.WHITE
    max_size: Optional[Coordinate] = None

    async def run(self, image: Image, text: str, context: Dict):
        if text.startswith('http://') or text.startswith('https://'):
            draw_image = DrawImage(plugin_input=self.plugin_input, position=self.position, max_size=self.max_size)
            return await draw_image.run(image, text, context)
        else:
            draw_text = DrawText(plugin_input=self.plugin_input, position=self.position,
                maxwidth=self.maxwidth, fontsize=self.fontsize, textstyle=self.textstyle)
            return await draw_text.run(image, text, context)
