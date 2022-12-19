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
from dataclasses import dataclass


log = logging.getLogger('memebot')


def name_equals_ignore_case(arg: str, role: discord.Role):
    return role.name.lower() == arg.lower()


# TODO: make this generic and work for both members and roles
@dataclass
class RoleMatch:
    role: discord.Role
    is_high_confindence: bool

    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        '''note: this is only looking at cached roles, so may not always work'''
        try:
            return cls(
                role=await commands.RoleConverter().convert(ctx, argument),
                is_high_confindence=True,
            )
        except commands.RoleNotFound:
            if not isinstance(argument, str) or not ctx.guild:
                raise
            roles = list(ctx.guild.roles)
            matching_roles = [role for role in roles if name_equals_ignore_case(argument, role)]
            if len(matching_roles) == 0:
                raise
            if len(matching_roles) > 1:  # too ambiguous
                raise                      # maybe another interaction is possible?
            return cls(
                role=matching_roles[0],
                is_high_confindence=len(roles) > 0,  # assuming role isn't missing
            )


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
    async def who_is(self, context: commands.Context, role_match: RoleMatch):
        '''Lists users with the given role'''
        str_list = '\n'.join(f'- {member.mention}' for member in role_match.role.members)
        str_message = f'{role_match.role.mention}:\n{str_list}'
        await context.send(str_message, allowed_mentions=discord.AllowedMentions.none())
