from .plugins import DrawText, TrimText, SpongifyText, AutoPosition, Coordinate, SplitText, StartsWithSelector, DrawImage, UserInput, RawInput, ContextInput
from .meme import Meme

ALL_MEMES = [
    Meme(
        image_filename='spongebob.jpg',
        aliases=['spongebob', 'sb'],
        plugins=[
            SpongifyText(plugin_input=UserInput()),
            DrawText(plugin_input=UserInput(), position=AutoPosition.BOTTOM)
        ]
    ),
    Meme(
        image_filename='mouthfeel.jpg',
        aliases=['mouthfeel'],
        plugins=[
            TrimText(plugin_input=UserInput(), numwords=1),
            DrawText(plugin_input=UserInput(), position=AutoPosition.BOTTOM, fontsize=72),
            DrawText(plugin_input=RawInput(text='Why is no one talking about the'), position=AutoPosition.TOP, maxwidth=40),
        ]
    ),
    Meme(
        image_filename='change-my-mind.jpg',
        aliases=['change my mind', 'change-my-mind'],
        plugins=[
            DrawText(plugin_input=UserInput(), position=Coordinate(x=316, y=256),
                maxwidth=15, fontsize=24, fontcolor='black', hastextoutline=False)
        ]
    ),
    Meme(
        image_filename='distracted-bf.jpg',
        aliases=['distracted bf', 'distracted-bf'],
        plugins=[
            SplitText(plugin_input=UserInput(), separator='/'),
            DrawText(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=198, y=310), maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=472, y=153), maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=682, y=300), maxwidth=12, fontsize=48)
        ]
    ),
    Meme(
        image_filename='brain.jpg',
        aliases=['brain'],
        plugins=[
            SplitText(plugin_input=UserInput(), separator=' /'),
            StartsWithSelector(
                plugin_input=ContextInput(key='text-1'),
                startswith='http',
                plugin_a=DrawImage(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=384, y=229)),
                plugin_b=DrawText(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=384, y=229),
                    maxwidth=15, fontsize=72, fontcolor='black', hastextoutline=False)),
            StartsWithSelector(
                plugin_input=ContextInput(key='text-2'),
                startswith='http',
                plugin_a=DrawImage(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=384, y=691)),
                plugin_b=DrawText(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=384, y=691),
                    maxwidth=15, fontsize=72, fontcolor='black', hastextoutline=False)),
            StartsWithSelector(
                plugin_input=ContextInput(key='text-3'),
                startswith='http',
                plugin_a=DrawImage(plugin_input=ContextInput(key='text-3'), position=Coordinate(x=384, y=1168)),
                plugin_b=DrawText(plugin_input=ContextInput(key='text-3'), position=Coordinate(x=384, y=1168),
                    maxwidth=12, fontsize=72, fontcolor='black', hastextoutline=False))
        ]
    ),
    Meme(
        image_filename='boromir.jpg',
        aliases=['one does not simply', 'simply', 'boromir'],
        plugins=[
            DrawText(plugin_input=UserInput(), position=AutoPosition.BOTTOM, fontsize=42),
            DrawText(plugin_input=RawInput(text='One does not simply'), position=AutoPosition.TOP, fontsize=42)
        ]
    )
]