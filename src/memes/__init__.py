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
        aliases=['mouthfeel'],
        plugins=[
            TrimText(numwords=1),
            DrawText(position=TextPosition.BOTTOM, fontsize=72),
            SetText(text='Why is no one talking about the', inputtextkey='headertext'),
            DrawText(position=TextPosition.TOP, maxwidth=40, inputtextkey='headertext'),
        ]
    ),
    Meme(
        image_filename='change-my-mind.jpg',
        aliases=['change my mind', 'change-my-mind'],
        plugins=[
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=316.5, y=256.5),
                maxwidth=15, fontsize=24, fontcolor='black', hastextoutline=False)
        ]
    ),
    Meme(
        image_filename='distracted-bf.jpg',
        aliases=['distracted bf', 'distracted-bf'],
        plugins=[
            SplitText(separator='/'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=198, y=310),
                maxwidth=15, fontsize=48, inputtextkey='text-0'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=472, y=153),
                maxwidth=15, fontsize=48, inputtextkey='text-1'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=682, y=300),
                maxwidth=12, fontsize=48, inputtextkey='text-2')
        ]
    ),
    Meme(
        image_filename='brain.jpg',
        aliases=['brain'],
        plugins=[
            SplitText(separator='/'),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=384, y=229),
                maxwidth=15, fontsize=72, inputtextkey='text-0', fontcolor='black', hastextoutline=False),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=384, y=691),
                maxwidth=15, fontsize=72, inputtextkey='text-1', fontcolor='black', hastextoutline=False),
            DrawText(position=TextPosition.CUSTOM, customposition=Coordinate(x=384, y=1168),
                maxwidth=12, fontsize=72, inputtextkey='text-2', fontcolor='black', hastextoutline=False)
        ]
    )
]
