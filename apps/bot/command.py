import discord
import logging
from pydantic import BaseModel
from typing import Callable, Awaitable

log = logging.getLogger('memebot')


CommandExecutor = Callable[[str, discord.abc.Messageable], Awaitable[None]]


class Command(BaseModel):
    name: str
    arg: str
    executor: CommandExecutor
    raw_command: str

    async def execute(self, messageable: discord.abc.Messageable):
        try:
            return await self.executor(self.arg, messageable)  # type: ignore
        except Exception:
            log.exception(f'error when executing command "{self.raw_command}"')
            await messageable.send('Something went wrong =(')