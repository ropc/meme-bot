import textwrap
import io
import os
import attr
import aiohttp
from contextlib import asynccontextmanager
from typing import Dict, AsyncContextManager
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, Position, find_centered_position, draw_outlined_text


@attr.s(kw_only=True)
class DrawImage(BasePlugin):
    position: Coordinate = attr.ib()
    size: Coordinate = attr.ib(default=None)
    session: aiohttp.ClientSession = attr.ib(factory=aiohttp.ClientSession)

    async def run(self, image: Image, context: Dict):
        url = context[self.inputtextkey]

        async with self.open_image(url) as custom_image:
            if self.size:
                #pylint: disable=no-member
                custom_image = custom_image.resize((self.size.x, self.size.y))

            size_x, size_y = custom_image.size[0], custom_image.size[1]
            #pylint: disable=no-member
            pos_x, pos_y = find_centered_position((self.position.x, self.position.y), (size_x, size_y))

            image.paste(custom_image, box=(pos_x, pos_y))

    @asynccontextmanager
    async def open_image(self, url) -> AsyncContextManager[Image.Image]: 
        #pylint: disable=no-member
        async with self.session.get(url) as response:
            image = Image.open(io.BytesIO(await response.read()))
        try:
            yield image
        finally:
            image.close()
