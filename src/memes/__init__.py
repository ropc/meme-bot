from .plugins import DrawText, TrimText, OverrideText, SpongifyText, TextPosition
from .change_my_mind import ChangeMyMind
from .basememe import BaseMeme
from .genericmeme import GenericMeme, MemeConfig
from .memeloader import MemeLoader


spongebob_config = MemeConfig(
    image_filename='spongebob.jpg',
    alias='spongebob',
    plugins=[
        SpongifyText(),
        DrawText(position=TextPosition.BOTTOM)
    ]
)

mouthfeel_config = MemeConfig(
    image_filename='mouthfeel.jpg',
    alias='mouthfeel',
    plugins=[
        TrimText(numwords=1),
        DrawText(position=TextPosition.BOTTOM, fontsize=72),
        OverrideText(text='Why is no one talking about the'),
        DrawText(position=TextPosition.TOP, maxwidth=40),
    ]
)
