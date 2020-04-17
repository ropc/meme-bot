import abc
from pydantic import BaseModel
from typing import Dict, Union
from PIL import Image
from .input import PluginInput


class BasePlugin(BaseModel, abc.ABC):
    plugin_input: PluginInput

    def get_input(self, context: Dict) -> str:
        return self.plugin_input.get_input(context)

    @abc.abstractmethod
    async def run(self, image: Image, context: Dict):
        pass
