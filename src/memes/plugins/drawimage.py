import textwrap
import io
import os
import attr
import aiohttp
from typing import Dict
from uuid import uuid4
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, Position, find_centered_position, draw_outlined_text


async def save_image(session, url) -> io.BufferedIOBase:
    async with session.get(url) as response:
        temp_image_path = f'{uuid4()}.jpg'
        with open(temp_image_path, 'wb+') as f:
            f.write(await response.read())
        return temp_image_path


@attr.s(kw_only=True)
class DrawImage(BasePlugin):
    position: Coordinate = attr.ib()
    size: Coordinate = attr.ib(default=None)

    async def run(self, image: Image, context: Dict):
        url = context[self.inputtextkey]

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                temp_image = io.BytesIO(await response.read())
            # temp_image_path = await save_image(session, url)

        with Image.open(temp_image) as custom_image:
            if self.size:
                #pylint: disable=no-member
                custom_image = custom_image.resize((self.size.x, self.size.y))

            size_x, size_y = custom_image.size[0], custom_image.size[1]
            #pylint: disable=no-member
            pos_x, pos_y = find_centered_position((self.position.x, self.position.y), (size_x, size_y))

            image.paste(custom_image, box=(pos_x, pos_y))

        # os.remove(temp_image_path)
        temp_image.close()
