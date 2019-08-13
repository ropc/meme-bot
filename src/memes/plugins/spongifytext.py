import attr
from PIL import Image
from .baseplugin import BasePlugin


@attr.s
class SpongifyText(BasePlugin):
    def draw(self, image: Image, text: str) -> str:
        vowels = set('aoeuiAOEUI')
        return ''.join(letter.lower() if letter in vowels else letter.upper() for letter in text)
