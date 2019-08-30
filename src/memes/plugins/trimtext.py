import attr
from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


@attr.s(kw_only=True)
class TrimText(BasePlugin):
    numwords: int = attr.ib()

    async def run(self, image: Image, context: Dict):
        text = context[self.inputtextkey]
        context[self.inputtextkey] = ''.join(text.split(' ')[:self.numwords])
