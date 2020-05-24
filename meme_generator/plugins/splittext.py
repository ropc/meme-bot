from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


class SplitText(BasePlugin):
    separator: str = '/'  # mypy: ignore

    async def run(self, image: Image, context: Dict):
        text = self.get_input(context)
        for (i, item) in enumerate(text.split(self.separator), 1):
            context[f'text-{i}'] = item.strip()
 