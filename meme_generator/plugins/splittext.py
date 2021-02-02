import re
from typing import Dict
from PIL import Image
from .baseplugin import BasePlugin


class SplitText(BasePlugin):
    regex = re.compile(r'(?:\s*/\s*|(https?://\S+))')

    class Config:
        arbitrary_types_allowed = True

    async def run(self, image: Image, text: str, context: Dict):
        non_empty_args = filter(None, self.regex.split(text))
        for (i, item) in enumerate(non_empty_args, 1):
            context[f'text-{i}'] = item.strip()
 