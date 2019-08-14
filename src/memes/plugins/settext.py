import attr
from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


@attr.s(kw_only=True)
class SetText(BasePlugin):
    text: str = attr.ib()

    def run(self, image: Image, context: Dict):
        context[self.inputtextkey] = self.text
