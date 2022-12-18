import asyncio
import datetime
import logging
import os
import random
import sys
import discord
import tailer
from discord.ext import commands
from memebot.guildconfig import MemeBotConfig
from typing import Optional


log = logging.getLogger('memebot')


class Meta(commands.Cog):

    def __init__(self, bot: commands.Bot, config: MemeBotConfig, log_filename: str):
        super().__init__()
        self.bot = bot
        self.config = config
        self.restart_message = 'Restarting...'
        self.log_filename = log_filename

    @commands.command()
    @commands.is_owner()
    async def restart(self, context: commands.Context):
        '''restart bot'''
        log.warning('restart command called')
        await context.send(self.restart_message)
        sys.exit(1)

    @commands.command()
    @commands.is_owner()
    async def logs(self, context: commands.Context, lines: int = 20, offset: int = 0):
        '''Output last lines of log. Usage: !logs [lines=20] [offset=0]'''
        with open(self.log_filename) as f:
            log_tail = tailer.tail(f, lines=lines + offset)[:lines]
            formatted_log_tail = '\n'.join(log_tail)[-1994:] # 2k char limit
            await context.send(f'```{formatted_log_tail}```')

    @commands.command(aliases=['whois', 'who is'])
    @commands.guild_only()
    async def who_is(self, context: commands.Context, role: discord.Role):
        '''Lists users with the given role'''
        str_list = '\n'.join(f'- {member.mention}' for member in role.members)
        str_message = f'{role.mention}:\n{str_list}'
        await context.send(str_message, allowed_mentions=discord.AllowedMentions.none())
