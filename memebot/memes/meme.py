import abc
import io
import os.path
import attr
from contextlib import asynccontextmanager
from typing import List, AsyncContextManager
from pathlib import Path
from PIL import Image
from .plugins import BasePlugin

# this will be something like ../meme-bot/src/memes
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[1])

@attr.s
class Meme:
    image_filename: str = attr.ib()
    aliases: List[str] = attr.ib()
    plugins: List[BasePlugin] = attr.ib()

    @asynccontextmanager
    async def generate(self, text) -> AsyncContextManager[io.BufferedIOBase]:
        meme_file = io.BytesIO()

        with Image.open(os.path.join(package_root_dir, 'assets', self.image_filename)) as image:  # type: Image.Image
            context = {'text': text}

            #pylint: disable=not-an-iterable
            for plugin in self.plugins:
                await plugin.run(image, context)

            image.save(meme_file, format=image.format)

        meme_file.seek(0)  # reset offset so that file can be read from the start

        try:
            yield meme_file
        finally:
            meme_file.close()
