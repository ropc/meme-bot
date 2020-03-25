import abc
import io
import logging
import os.path
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List, AsyncContextManager
from pathlib import Path
from PIL import Image
from .plugins import BasePlugin, USER_INPUT_KEY

# this will be something like ../meme-bot/src/memes
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[1])

log = logging.getLogger()


class Meme(BaseModel):
    image_filename: str
    aliases: List[str]
    plugins: List[BasePlugin]

    @asynccontextmanager
    async def generate(self, text):
        meme_file = io.BytesIO()

        with Image.open(os.path.join(package_root_dir, 'assets', self.image_filename)) as image:  # type: Image.Image
            context = {USER_INPUT_KEY: text}

            for plugin in self.plugins:
                log.debug(f'Meme context: {context}, next plugin: {plugin}')
                await plugin.run(image, context)

            image.save(meme_file, format=image.format)

        meme_file.seek(0)  # reset offset so that file can be read from the start

        try:
            yield meme_file
        finally:
            meme_file.close()
