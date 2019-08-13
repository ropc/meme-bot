import abc
from PIL import Image


class BasePlugin(abc.ABC):
    @abc.abstractmethod
    def draw(self, image: Image, text: str) -> str:
        raise NotImplementedError()
