import abc
import attr
from typing import Dict
from PIL import Image


@attr.s(kw_only=True)
class BasePlugin(abc.ABC):
    inputtextkey: str = attr.ib(default='text')

    @abc.abstractmethod
    async def run(self, image: Image, context: Dict):
        raise NotImplementedError()
