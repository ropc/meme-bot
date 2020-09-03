import urllib.parse
import aiohttp
import discord
from discord.ext import commands

class WolframAlpha(commands.Cog):

    def __init__(self, app_id: str):
        self.app_id = app_id

    @commands.command(aliases=["wolfram", "wa"])
    async def wolframalpha(self, context: commands.Context, *, text: str):
        '''Run a query on wolframalpha'''
        async with context.typing():
            parsed_text = urllib.parse.quote(text)
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.wolframalpha.com/v1/result?i={parsed_text}&appid={self.app_id}') as resp:
                    response = await resp.text()
                    await context.send(response)
