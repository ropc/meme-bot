from typing import Dict, Callable, TypeVar
from PIL import Image
from . import BasePlugin


class StartsWithSelector(BasePlugin):
    startswith: str
    plugin_a: BasePlugin
    plugin_b: BasePlugin

    async def run(self, image: Image, context: Dict):
        input_text = self.get_input(context)
        plugin = self.plugin_a if input_text.startswith(self.startswith) else self.plugin_b
        await plugin.run(image, context)
