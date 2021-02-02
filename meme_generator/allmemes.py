from .plugins import DrawText, TrimText, SpongifyText, AutoPosition, Coordinate, SplitText, DrawImage, UserInput, RawInput, ContextInput, TextStyle, DrawInput
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
                maxwidth=15, fontsize=24, textstyle=TextStyle.BLACK)
        ]
    ),
    Meme(
        image_filename='distracted-bf.jpg',
        aliases=['distracted bf', 'distracted-bf'],
        help_string='Usage: !meme distracted bf <text1> / <text2> / <text3>',
        plugins=[
            SplitText(plugin_input=UserInput(), separator='/'),
            DrawText(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=198, y=310),
                maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=472, y=153),
                maxwidth=15, fontsize=48),
            DrawText(plugin_input=ContextInput(key='text-3'), position=Coordinate(x=682, y=300),
                maxwidth=12, fontsize=48)
        ]
    ),
    Meme(
        image_filename='brain.jpg',
        aliases=['brain'],
        help_string='Usage: !meme brain <text1> / <text2> / <text3>',
        plugins=[
            SplitText(plugin_input=UserInput(), separator=' /'),
            DrawInput(plugin_input=ContextInput(key='text-1'), position=Coordinate(x=384, y=229),
                    maxwidth=15, fontsize=72, textstyle=TextStyle.BLACK,
                    max_size=Coordinate(x=762, y=450)),
            DrawInput(plugin_input=ContextInput(key='text-2'), position=Coordinate(x=384, y=691),
                maxwidth=15, fontsize=72, textstyle=TextStyle.BLACK,
                max_size=Coordinate(x=762, y=450)),
            DrawInput(plugin_input=ContextInput(key='text-3'), position=Coordinate(x=384, y=1168),
                    maxwidth=12, fontsize=72, textstyle=TextStyle.BLACK,
                    max_size=Coordinate(x=762, y=450)),
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
                maxwidth=9,
                textstyle=TextStyle.BLACK),
            DrawText(plugin_input=ContextInput(key='text-2'),
                position=Coordinate(x=356, y=99),
                maxwidth=9,
                textstyle=TextStyle.BLACK),
            DrawText(plugin_input=ContextInput(key='text-3'),
                position=Coordinate(x=308, y=617)),
        ]
    ),
    Meme(
        image_filename='is-this-a-pigeon.jpg',
        aliases=['is this'],
        help_string='Usage: !meme is this <a pidgeon> / <text on butterfly> / <text on face>',
        plugins=[
            SplitText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='text-1', prefix='is this ', suffix='?'),
                position=AutoPosition.BOTTOM, fontsize=62),
            DrawText(plugin_input=ContextInput(key='text-2'),
                position=Coordinate(x=834, y=196), fontsize=62, maxwidth=12),
            DrawText(plugin_input=ContextInput(key='text-3'),
                position=Coordinate(x=294, y=409), fontsize=62),
        ]
    ),
    Meme(
        image_filename='nut-button.jpg',
        aliases=['nut button', 'blue button'],
        help_string='Usage: !meme nut button <text on button> / <optional: text on hand> / <optional: text above meme>',
        plugins=[
            SplitText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='text-1'),
                position=Coordinate(x=975, y=1600), fontsize=270),
            DrawText(plugin_input=ContextInput(key='text-2'), required=False,
                position=Coordinate(x=2200, y=1345), fontsize=320, maxwidth=10),
            DrawText(plugin_input=ContextInput(key='text-3'), required=False,
                position=AutoPosition.TOP, fontsize=300, maxwidth=12)
        ]
    ),
    Meme(
        image_filename='shaking-hands.jpg',
        aliases=['shaking hands', 'sh'],
        help_string='Usage: !meme shaking hands <left> / <hands> / <right>',
        plugins=[
            SplitText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='text-1'),
                position=Coordinate(x=180, y=360), fontsize=62, maxwidth=10),
            DrawText(plugin_input=ContextInput(key='text-2'),
                position=Coordinate(x=349, y=100), fontsize=62, maxwidth=10),
            DrawText(plugin_input=ContextInput(key='text-3'),
                position=Coordinate(x=710, y=300), fontsize=62, maxwidth=11),
        ]
    ),
    Meme(
        image_filename='drake.jpg',
        aliases=['drake'],
        help_string='Usage: !meme drake <top> / <bottom>',
        plugins=[
            SplitText(plugin_input=UserInput()),
            DrawText(plugin_input=ContextInput(key='text-1'), textstyle=TextStyle.BLACK,
                position=Coordinate(x=900, y=300), fontsize=84, maxwidth=12),
            DrawText(plugin_input=ContextInput(key='text-2'), textstyle=TextStyle.BLACK,
                position=Coordinate(x=900, y=900), fontsize=84, maxwidth=12),
        ]
    ),
]