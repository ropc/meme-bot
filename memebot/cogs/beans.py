import logging
import os
import re
import discord
from discord.ext import commands
from typing import Set
from .quote import format_quote_embed


log = logging.getLogger('memebot')


class Beans(commands.Cog):
    def __init__(self):
        self._ids: Set[int] = set(int(_id) for _id in os.getenv('MEME_BOT_BEANS_HOOK_IDS', '').split(','))
        self._regex = re.compile(r'\bb(\s*)e(\s*)a(\s*)n((\s*)s)?\b', flags=re.IGNORECASE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id not in self._ids:
            return
        if len(message.content) < 30:
            return  # too short, not worth commenting
        matches = self._regex.finditer(message.content)
        if not any(_group_elements_match(match) for match in matches):
            return
        try:
            await message.add_reaction('\N{no entry}')
        except discord.HTTPException:
            log.info('Could not add reaction to beans message', exc_info=True)

        embed = format_quote_embed(message)
        embed.title = ':warning: WARNING: MESSAGE LOOKS LIKE A BEANS POST. READ AT YOUR OWN RISK :warning:'
        await message.channel.send(embed=embed)


def _group_elements_match(match: re.Match):
    bean_singular_spacing_matches = match.group(5) is None and match.group(1) == match.group(2) == match.group(3)
    bean_plural_spacing_matches = match.group(1) == match.group(2) == match.group(3) == match.group(5)
    return bean_singular_spacing_matches or bean_plural_spacing_matches
