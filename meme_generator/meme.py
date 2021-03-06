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

# this will be something like ../memebot/meme_generator
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[0])

log = logging.getLogger('memebot')


class Meme(BaseModel):
    image_filename: str
    aliases: List[str]
    plugins: List[BasePlugin]
    help_string: str

    @asynccontextmanager
    async def generate(self, text):
        meme_file = io.BytesIO()

        with Image.open(os.path.join(package_root_dir, 'assets', self.image_filename)) as image:  # type: Image.Image
            context = {USER_INPUT_KEY: text}

            for plugin in self.plugins:
                input_text = plugin.plugin_input.get_input(context)

                log.debug(f'Plugin input text: {input_text}, context: {context}, plugin: {plugin!r}')

                if input_text is not None:
                    await plugin.run(image, input_text, context)
                elif plugin.required:
                    raise ValueError(f'Missing input for required plugin: {plugin}')

            image.save(meme_file, format=image.format)

        meme_file.seek(0)  # reset offset so that file can be read from the start
        try:
            yield meme_file
        finally:
            meme_file.close()
