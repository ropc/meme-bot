import attr
from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


@attr.s(kw_only=True)
class SplitText(BasePlugin):
    separator: str = attr.ib()

    def draw(self, image: Image, context: Dict):
        text = context[self.inputtextkey]
        for (i, item) in enumerate(text.split(self.separator)):
            context[f'text-{i}'] = item.strip()
 