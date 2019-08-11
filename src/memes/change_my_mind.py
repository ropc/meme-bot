import abc
import io
import os
import re
import uuid
import textwrap
from pathlib import Path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .utils import find_centered_position


# this will be something like ../meme-bot/src/memes
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[1])


def meme_generator(meme_text) -> str:
    meme_image_path = f'spongebob-{uuid.uuid4()}.jpg'
    meme_text = textwrap.fill(meme_text, 20)
    
    with open(os.path.join(package_root_dir, 'assets', 'change-my-mind.jpg'), 'rb') as f:
        img = Image.open(io.BytesIO(f.read()))
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype('Impact', 24)

        # ideal positions (absolute values)
        topleft = (206, 205)
        center = (316.5, 256.5)

        position = find_centered_position(topleft, center, draw.textsize(meme_text, font=font))
        draw.multiline_text(position, meme_text, fill='black', font=font, align='center')

        img.save(meme_image_path, format='JPEG')
    return meme_image_path
