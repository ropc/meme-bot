from typing import Union
from pydantic import BaseModel
from enum import Enum, auto
from PIL import ImageFont
from PIL import ImageDraw


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class Coordinate(BaseModel):
    x: int
    y: int


class AutoPosition(AutoName):
    TOP = auto()
    CENTER = auto()
    BOTTOM = auto()


Position = Union[AutoPosition, Coordinate]


def draw_outlined_text(draw: ImageDraw, position, text: str, **kwargs):
    x, y = position
    shadowcolor = 'black'
    nonfill_kargs = {k:v for (k, v) in kwargs.items() if k != 'fill'}  # gross
    draw.multiline_text((x-1, y-1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y-1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x-1, y+1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text((x+1, y+1), text, fill=shadowcolor, align='center', spacing=4, **nonfill_kargs)
    draw.multiline_text(position, text, align='center', spacing=4, **kwargs)


def find_centered_position(center, size):
    offset_x = _find_offset(size[0], center[0])
    offset_y = _find_offset(size[1], center[1])
    return (offset_x, offset_y)


def _find_offset(length, center):
    return int(center - (length / 2))
