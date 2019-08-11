import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .utils import find_centered_position
from .basememe import BaseMeme


class ChangeMyMind(BaseMeme):

    def image_filename(self):
        return 'change-my-mind.jpg'

    def draw_meme(self, image: Image, text: str):
        text = textwrap.fill(text, 20)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('Impact', 24)

        # ideal positions (absolute values)
        topleft = (206, 205)
        center = (316.5, 256.5)

        position = find_centered_position(topleft, center, draw.textsize(text, font=font))
        draw.multiline_text(position, text, fill='black', font=font, align='center')
