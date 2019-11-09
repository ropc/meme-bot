from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


class TrimText(BasePlugin):
    numwords: int
    output_key: str = 'trimmed-text'

    async def run(self, image: Image, context: Dict):
        text = self.get_input(context)
        context[self.output_key] = ''.join(text.split(' ')[:self.numwords])
