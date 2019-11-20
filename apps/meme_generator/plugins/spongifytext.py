from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


class SpongifyText(BasePlugin):
    output_key: str = 'spongified-text'

    async def run(self, image: Image, context: Dict):
        vowels = set('aoeuiAOEUI')
        text = self.get_input(context)
        context[self.output_key] = ''.join(letter.lower() if letter in vowels else letter.upper() for letter in text)
