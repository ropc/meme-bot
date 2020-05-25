import abc
from pydantic import BaseModel
from typing import Dict, Union
from PIL import Image
from .input import AbstractInput


class BasePlugin(BaseModel, abc.ABC):
    plugin_input: AbstractInput
    required: bool = True

    @abc.abstractmethod
    async def run(self, image: Image, text: str, context: Dict):
        pass
