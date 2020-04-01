import discord
import abc
import logging
from pydantic import BaseModel
from typing import Callable, Awaitable, Optional

log = logging.getLogger('memebot')


ExecutorCallable = Callable[[str, discord.abc.Messageable], Awaitable[None]]


class CommandExecutor(abc.ABC):
    @abc.abstractmethod
    def __call__(self, command_arg: str, messageable: discord.abc.Messageable) -> Awaitable[None]:
        pass

    @abc.abstractmethod
    def help_string(self) -> str:
        pass


def executor(help_string: Optional[str]=None):
    def internal_executor(func: ExecutorCallable) -> CommandExecutor:
        class _CE(CommandExecutor):
            def __call__(self, command_arg: str, messageable: discord.abc.Messageable) -> Awaitable[None]:
                return func(command_arg, messageable)
            def help_string(self) -> str:
                return help_string if help_string else (func.__doc__ if func.__doc__ else '')
        return _CE()
    return internal_executor


class Command(BaseModel):
    name: str
    arg: str
    executor: CommandExecutor
    raw_command: str

    class Config:
        arbitrary_types_allowed = True

    async def execute(self, messageable: discord.abc.Messageable):
        try:
            return await self.executor(self.arg, messageable)  # type: ignore
        except Exception:
            log.exception(f'error when executing command "{self.raw_command}"')
            await messageable.send(f'Something went wrong =(\nAttempted to use command "{self.name}": {self.executor.help_string()}')
