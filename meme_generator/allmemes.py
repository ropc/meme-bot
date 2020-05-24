from .plugins import DrawText, TrimText, SpongifyText, AutoPosition, Coordinate, SplitText, StartsWithSelector, DrawImage, UserInput, RawInput, ContextInput
from .meme import Meme


ALL_MEMES = [
    Meme(
        image_filename='spongebob.jpg',
        aliases=['spongebob', 'sb'],
        help_string='Usage: !meme spongebob <text>',
        plugins=[
            SpongifyText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='spongified-text'), position=AutoPosition.BOTTOM)
        ]
    ),
    Meme(
        image_filename='mouthfeel.jpg',
        aliases=['mouthfeel'],
        help_string='Usage: !meme mouthfeel <single word>',
        plugins=[
            TrimText(plugin_input=UserInput(), numwords=1),
            DrawText(plugin_input=ContextInput(key='trimmed-text'), position=AutoPosition.BOTTOM, fontsize=72),
            DrawText(plugin_input=RawInput(text='Why is no one talking about the'), position=AutoPosition.TOP, maxwidth=40),
        ]
    ),
    Meme(
        image_filename='change-my-mind.jpg',
        aliases=['change my mind', 'change-my-mind'],
        help_string='Usage: !meme change my mind <text>',
        plugins=[
            DrawText(plugin_input=UserInput(), position=Coordinate(x=316, y=256),
                maxwidth=15, fontsize=24, fontcolor='black', hastextoutline=False)
        ]
    ),
    Meme(
        image_filename='distracted-bf.jpg',
        aliases=['distracted bf', 'distracted-bf'],
        help_string='Usage: !meme distracted bf <text1> / <text2> / <text3>',
        plugins=[
            SplitText(plugin_input=UserInput(), separator='/'),
            DrawText(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=198, y=310), maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=472, y=153), maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-3'), position=Coordinate(x=682, y=300), maxwidth=12, fontsize=48)
        ]
    ),
    Meme(
        image_filename='brain.jpg',
        aliases=['brain'],
        help_string='Usage: !meme brain <text1> / <text2> / <text3>',
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
        help_string='Usage: !meme one does not simply <text>',
        plugins=[
            DrawText(plugin_input=UserInput(), position=AutoPosition.BOTTOM, fontsize=42),
            DrawText(plugin_input=RawInput(text='One does not simply'), position=AutoPosition.TOP, fontsize=42)
        ]
    ),
    Meme(
        image_filename='two-buttons.jpg',
        aliases=['two buttons', 'buttons'],
        help_string='Usage: !meme two buttons <option 1> / <option 2> / <person>',
        plugins=[
            SplitText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='text-1'),
                position=Coordinate(x=166, y=143),
                fontcolor='black', hastextoutline=False),
            DrawText(plugin_input=ContextInput(key='text-2'),
                position=Coordinate(x=347, y=99),
                fontcolor='black', hastextoutline=False),
            DrawText(plugin_input=ContextInput(key='text-3'),
                position=Coordinate(x=308, y=617),
                fontcolor='black', hastextoutline=False),
        ]
    )
]