from .spongebob import SpongeBob
from .change_my_mind import ChangeMyMind
from .mouthfeel import Mouthfeel
from .basememe import BaseMeme
from .genericmeme import GenericMeme, MemeConfig, SpongifyText, Text, TextPosition

sb_top = MemeConfig(image_filename='spongebob.jpg', plugins=[SpongifyText(), Text(position=TextPosition.TOP)])
sb_center = MemeConfig(image_filename='spongebob.jpg', plugins=[SpongifyText(), Text(position=TextPosition.CENTER)])
sb_bottom = MemeConfig(image_filename='spongebob.jpg', plugins=[SpongifyText(), Text(position=TextPosition.BOTTOM)])
sb_text = MemeConfig(image_filename='spongebob.jpg', plugins=[SpongifyText(), Text(hasborder=False)])
sb_nottext = MemeConfig(image_filename='spongebob.jpg', plugins=[Text()])
