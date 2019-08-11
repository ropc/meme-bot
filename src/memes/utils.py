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