from typing import Union
from .baseplugin import BasePlugin
from .input import UserInput, RawInput, ContextInput, USER_INPUT_KEY
from .drawtext import DrawText
from .drawimage import DrawImage
from .spongifytext import SpongifyText
from .trimtext import TrimText
from .splittext import SplitText
from .selector import StartsWithSelector
from .utils import Position, Coordinate, AutoPosition

AnyPlugin = Union[StartsWithSelector, SplitText, DrawImage, DrawText, TrimText, SpongifyText]
