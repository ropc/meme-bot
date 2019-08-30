import attr
from enum import IntEnum
from PIL import ImageFont
from PIL import ImageDraw


@attr.s
class Coordinate:
    x: float = attr.ib()
    y: float = attr.ib()


class Position(IntEnum):
    TOP = 1
    CENTER = 2
    BOTTOM = 3
    CUSTOM = 4


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
    return center - (length / 2)
