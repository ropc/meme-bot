import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .utils import draw_outlined_text
from .basememe import BaseMeme

class Mouthfeel(BaseMeme):

    def image_filename(self):
        return 'mouthfeel.jpg'

    def draw_meme(self, image: Image, text: str):
        text = textwrap.fill(text, 20)
        draw = ImageDraw.Draw(image)
        header_font = ImageFont.truetype('Impact', 48)

        img_x, img_y = image.size
        textsize_x, textsize_y = draw.textsize(text, font=header_font)
        position = ((img_x - textsize_x) / 2, (img_y * 0.95) - textsize_y)

        header_text = 'Why is no one talking about the'
        # size_x, _ = draw.textsize(text, font=header_font)

        draw_outlined_text(draw, (0, 0), header_font, header_text)
        draw_outlined_text(draw, position, ImageFont.truetype('Impact', 64), text.split()[0])
