from PIL import ImageFont
from PIL import ImageDraw

def draw_outlined_text(draw: ImageDraw, position, font: ImageFont, text: str):
    x, y = position
    shadowcolor = 'black'
    draw.multiline_text((x-1, y-1), text, font=font, fill=shadowcolor, align='center', spacing=4)
    draw.multiline_text((x+1, y-1), text, font=font, fill=shadowcolor, align='center', spacing=4)
    draw.multiline_text((x-1, y+1), text, font=font, fill=shadowcolor, align='center', spacing=4)
    draw.multiline_text((x+1, y+1), text, font=font, fill=shadowcolor, align='center', spacing=4)
    draw.multiline_text(position, text, font=font, align='center', spacing=4)

def find_centered_position(topleft, center, size):
    offset_x = _find_offset(topleft[0], size[0], center[0])
    offset_y = _find_offset(topleft[1], size[1], center[1])
    return (topleft[0] + offset_x, topleft[1] + offset_y)

def _find_offset(topleft, length, center):
    actualcenter = topleft + (length / 2)
    return center - actualcenter