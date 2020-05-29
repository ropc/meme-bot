import discord
import abc
import logging
from pydantic import BaseModel
from typing import Callable, Awaitable, Optional, Iterable

log = logging.getLogger('memebot')


ExecutorCallable = Callable[['UserCommand', discord.abc.Messageable], Awaitable[None]]


class CommandExecutor(abc.ABC):
    @abc.abstractmethod
    def __call__(self, command: 'UserCommand', messageable: discord.abc.Messageable) -> Awaitable[None]:
        pass

    @abc.abstractmethod
    def help_string(self) -> str:
        pass


class CommandEntry(BaseModel):
    executor: CommandExecutor
    aliases: Iterable[str]

    class Config:
        arbitrary_types_allowed = True


def create_embed(*, commands: Iterable[CommandEntry], **kwargs) -> discord.Embed:
    embed = discord.Embed(**kwargs)
    for entry in commands:
        embed.add_field(
            name=', '.join(f'**{a}**' for a in entry.aliases),
            value='\n'.join(line.strip() for line in entry.executor.help_string().splitlines()),
            inline=False)
    return embed


def executor(help_string: Optional[str]=None):
    def internal_executor(func: ExecutorCallable) -> CommandExecutor:
        class _CE(CommandExecutor):
            def __call__(self, command: 'UserCommand', messageable: discord.abc.Messageable) -> Awaitable[None]:
                if command.arg == '--help' or command.arg == '-h':
                    embed = create_embed(commands=[CommandEntry(executor=self, aliases=[command.name])])
                    return messageable.send(embed=embed)
                return func(command, messageable)

            def help_string(self) -> str:
                if help_string:
                    return help_string.strip()
                if func.__doc__:
                    return func.__doc__.strip()
                return ''

        return _CE()
    return internal_executor


class UserCommand(BaseModel):
    name: str
    arg: str
    executor: CommandExecutor
    initiator: discord.abc.User
    raw_command: str

    class Config:
        arbitrary_types_allowed = True

    async def execute(self, messageable: discord.abc.Messageable):
        try:
            return await self.executor(self, messageable)
        except Exception:
            log.exception(f'error when executing command "{self.raw_command}"')
            embed = create_embed(
                commands=[CommandEntry(executor=self.executor, aliases=[self.name])],
                title='Something went wrong :cry:',
                description=f'Input: `{self.raw_command}`')
            await messageable.send(embed=embed)
