from .plugins import DrawText, TrimText, SetText, SpongifyText, TextPosition, Coordinate, SplitText
from .meme import Meme

ALL_MEMES = [
    Meme(
        image_filename='spongebob.jpg',
        aliases=['spongebob', 'sb'],
        plugins=[
            SpongifyText(),
            DrawText(position=TextPosition.BOTTOM)
        ]
    ),
    Meme(
        image_filename='mouthfeel.jpg',
        alias=['mouthfeel'],
        plugins=[
            TrimText(numwords=1),
            DrawText(position=TextPosition.BOTTOM, fontsize=72),
            SetText(text='Why is no one talking about the', inputtextkey='headertext'),
            DrawText(position=TextPosition.TOP, maxwidth=40, inputtextkey='headertext'),
        ]
    ),
    Meme(
        image_filename='change-my-mind.jpg',
        alias=['change my mind', 'change-my-mind'],
        plugins=[
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=316.5, y=256.5),
                maxwidth=15, fontsize=24, fontcolor='black', hasborder=False)
        ]
    ),
    Meme(
        image_filename='distracted-bf.jpg',
        alias=['distracted bf', 'distracted-bf'],
        plugins=[
            SplitText(separator='/'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=198, y=310),
                maxwidth=15, fontsize=48, inputtextkey='text-0'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=472, y=153),
                maxwidth=15, fontsize=48, inputtextkey='text-1'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=682, y=300),
                maxwidth=15, fontsize=48, inputtextkey='text-2')
        ]
    )
]
