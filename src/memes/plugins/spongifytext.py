import attr
from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


@attr.s(kw_only=True)
class SpongifyText(BasePlugin):
    def run(self, image: Image, context: Dict):
        vowels = set('aoeuiAOEUI')
        text = context[self.inputtextkey]
        context[self.inputtextkey] = ''.join(letter.lower() if letter in vowels else letter.upper() for letter in text)
