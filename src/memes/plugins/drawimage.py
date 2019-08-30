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


async def saveimage(session, url) -> str:
    async with session.get(url) as response:
        image_data = await response.read()
        temp_image_path = str(uuid4())
        with open(temp_image_path, 'wb+') as f:
            f.write(image_data)
        print('saved image')
        return temp_image_path


@attr.s(kw_only=True)
class DrawImage(BasePlugin):
    position: Coordinate = attr.ib(default=None)

    async def run(self, image: Image, context: Dict):
        url = context[self.inputtextkey]
        print('running drawimage at', url)

        async with aiohttp.ClientSession() as session:
            temp_image_path = await saveimage(session, url)

        with open(temp_image_path, 'rb') as f:
            custom_image = Image.open(io.BytesIO(f.read()))

            print('pasting image at', self.position)
            #pylint: disable=no-member
            image.paste(custom_image, box=(self.position.x, self.position.y))

        os.remove(temp_image_path)
