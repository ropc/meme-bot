import re
import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .utils import draw_outlined_text
from .basememe import BaseMeme

class SpongeBob(BaseMeme):

    def image_filename(self):
        return 'spongebob.jpg'

    def draw_meme(self, image: Image, text: str):
        text = textwrap.fill(spongify_text(text), 20)

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('Impact', 48)

        img_x, img_y = image.size
        textsize_x, textsize_y = draw.textsize(text, font=font)
        position = ((img_x - textsize_x) / 2, (img_y * 0.95) - textsize_y)

        draw_outlined_text(draw, position, font, text)


def spongify_text(text: str):
    return re.sub('([AOEUI])', lambda x: x.group(1).lower(), text.upper())
