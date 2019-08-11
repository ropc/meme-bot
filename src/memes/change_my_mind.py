import abc
import io
import re
import uuid
import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from utils import draw_outlined_text


def spogebob_meme(meme_text) -> str:
    meme_image_path = f'spongebob-{uuid.uuid4()}.jpg'
    meme_text = textwrap.fill(spongify_text(meme_text), 20)
    with open('../../assets/spongebob.jpg', 'rb') as f:
        img = Image.open(io.BytesIO(f.read()))
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype('Impact', 48)

        img_x, _ = img.size
        textsize_x, textsize_y = draw.textsize(meme_text, font=font)
        position = ((img_x - textsize_x) / 2, (img.size[1] * 0.95) - textsize_y)

        draw_outlined_text(draw, position, font, meme_text)

        img.save(meme_image_path, format='JPEG')
    return meme_image_path


def spongify_text(text: str):
    return re.sub('([AOEUI])', lambda x: x.group(1).lower(), text.upper())
