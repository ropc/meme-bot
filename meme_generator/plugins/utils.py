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


def find_centered_position(center, size):
    offset_x = _find_offset(size[0], center[0])
    offset_y = _find_offset(size[1], center[1])
    return (offset_x, offset_y)


def _find_offset(length, center):
    return int(center - (length / 2))
