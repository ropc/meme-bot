import argparse
import asyncio
import logging
import ptvsd
import io
from PIL import Image
from pygtrie import CharTrie
from .meme import Meme
from .allmemes import ALL_MEMES

logging.basicConfig(format='%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s')
log = logging.getLogger()
log.setLevel(logging.DEBUG)


async def _run_generator(meme: Meme, text: str):
    async with meme.generate(text) as image:  # type: io.BytesIO
        with Image.open(image) as pillow_image:  # type: Image.Image
            pillow_image.show()


def run_meme():
    parser = argparse.ArgumentParser()
    parser.add_argument('command',  nargs='+', help="meme command. this does not need '!meme'")
    parser.add_argument('-w', '--wait', action='store_true', default=False)
    args = parser.parse_args()

    log.debug(f'debug args: {args}')

    ptvsd.enable_attach()
    if args.wait:
        ptvsd.wait_for_attach()

    # create dict of memes
    # TODO: have this work closer to how it works in memebot.py
    memes = CharTrie()
    for meme in ALL_MEMES:
        for alias in meme.aliases:
            memes[alias] = meme

    # run given meme
    command = ' '.join(args.command).strip()
    alias, meme = memes.longest_prefix(command)
    if not alias or not meme:
        log.error('no such meme found')
        exit(1)

    text = command[len(alias):].strip()
    asyncio.run(_run_generator(meme, text))

