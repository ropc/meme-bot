import abc
import io
import os.path
import uuid
import attr
from typing import List
from pathlib import Path
from PIL import Image
from .plugins import BasePlugin

# this will be something like ../meme-bot/src/memes
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[1])

@attr.s
class Meme:
    image_filename: str = attr.ib()
    alias: str = attr.ib()
    plugins: List[BasePlugin] = attr.ib()

    def generate(self, text):
        meme_unique_image_path = f'{self.image_filename}-{uuid.uuid4()}.jpg'

        with open(os.path.join(package_root_dir, 'assets', self.image_filename), 'rb') as f:
            image = Image.open(io.BytesIO(f.read()))
            context = {'text': text}

            #pylint: disable=not-an-iterable
            for plugin in self.plugins:
                plugin.draw(image, context)

            image.save(meme_unique_image_path, format='JPEG')

        return meme_unique_image_path
