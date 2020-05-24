import textwrap
import io
import os
import math
import aiohttp
from contextlib import asynccontextmanager
from pydantic import Field
from typing import Dict, Optional
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from .baseplugin import BasePlugin
from .utils import Coordinate, find_centered_position

session = aiohttp.ClientSession()

class DrawImage(BasePlugin):
    position: Coordinate
    max_size: Optional[Coordinate] = None

    async def run(self, image: Image, context: Dict):
        url = self.get_input(context)

        async with self.open_image(url) as custom_image:
            max_size_x = self.max_size.x if self.max_size else image.size[0] // 2
            max_size_y = self.max_size.y if self.max_size else image.size[1] // 2

            resize_ratio = min(max_size_x / custom_image.size[0], max_size_y / custom_image.size[1])

            size_x = math.floor(custom_image.size[0] * resize_ratio)
            size_y = math.floor(custom_image.size[1] * resize_ratio)

            if (size_x, size_y) != custom_image.size:
                custom_image = custom_image.resize((size_x, size_y), resample=Image.LANCZOS)

            size_x, size_y = custom_image.size[0], custom_image.size[1]
            pos_x, pos_y = find_centered_position((self.position.x, self.position.y), (size_x, size_y))

            image.paste(custom_image, box=(pos_x, pos_y))

    @asynccontextmanager
    async def open_image(self, url): 
        async with session.get(url) as response:
            image = Image.open(io.BytesIO(await response.read()))
        try:
            yield image
        finally:
            image.close()
