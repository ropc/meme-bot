from .plugins import DrawText, TrimText, OverrideText, SpongifyText, TextPosition, Coordinate
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

change_my_mind_config = MemeConfig(
    image_filename='change-my-mind.jpg',
    alias='change-my-mind',
    plugins=[
        DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=316.5, y=256.5),
            maxwidth=15, fontsize=24, fontcolor='black', hasborder=False)
    ]
)
