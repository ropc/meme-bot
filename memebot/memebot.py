import os
import logging
import discord
from discord.ext import commands
from discord.ext.commands.view import StringView
from pygtrie import CharTrie
from typing import Dict, Iterable, Callable, Awaitable, Optional, MutableMapping, Tuple, Mapping, List
from .guildconfig import get_guild_config_dict
from .cogs import Quote, OutOfContext, ChatStats, RollDice, Player, Beans, Meme, Meta, TarotCard, WolframAlpha, Suggest, Reminder, Hey
from .cogs.meme import MemeGroup
from .error import MemeBotError
from .help import EmbedHelpCommand, add_single_command_field


LOG_FILE = '/tmp/memebot.log'
LOG_FORMAT = '%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s'

logging.basicConfig(format=LOG_FORMAT)
logging.getLogger().setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.getLogger().addHandler(file_handler)

log = logging.getLogger('memebot')
log.setLevel(logging.DEBUG)


class MemeBot(commands.Bot):

    def __init__(self, command_prefix, help_command=EmbedHelpCommand(), description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        # make sure this is a Trie
        self.all_commands = CharTrie(self.all_commands)

        config = get_guild_config_dict(os.getenv('MEME_BOT_GUILD_CONFIG', '{}'))

        # cogs setup
        # TODO: this needs auto dependency management
        ooc_cog = OutOfContext(self, int(os.getenv('MEME_BOT_OOC_CHANNEL_ID', 0)))
        self.add_cog(Quote())
        self.add_cog(ooc_cog)
        self.add_cog(ChatStats())
        self.add_cog(RollDice(int(x) for x in os.getenv('MEME_BOT_UNLUCKY_ROLL_IDS', '').split(',') if x))
        self.add_cog(Player(self, config))
        self.add_cog(Meme(self))
        self.add_cog(Beans())
        self.add_cog(Meta(self, config, LOG_FILE))
        self.add_cog(WolframAlpha(os.getenv('MEME_BOT_WOLFRAM_ALPHA_KEY', '')))
        self.add_cog(TarotCard())
        self.add_cog(Suggest(os.getenv('MEME_BOT_GITHUB_TOKEN', ''), os.getenv('MEME_BOT_SUGGESTION_GITHUB_PROJECT_COLUMN_ID', '')))
        self.add_cog(Reminder(self, os.getenv('REMINDERS_SAVE_FILE_PATH', './reminders.pickle')))
        self.add_cog(Hey(ooc_cog=ooc_cog))

    async def on_command(self, context: commands.Context):
        log.debug(f'received command {context.command}')

    async def on_command_completion(self, context: commands.Context):
        log.debug(f'successfully completed command {context.command}')

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError):
        log.error(f'command error for {context.command}', exc_info=exception)
        if isinstance(exception, MemeBotError) and len(exception.args) > 0 and isinstance(exception.args[0], str):
            embed = discord.Embed(
                title=exception.args[0],
                description=f'Input: `{context.message.content}`')
            await context.send(embed=embed)
        elif context.command:
            embed = discord.Embed(
                title='Something went wrong :cry:',
                description=f'Input: `{context.message.content}`')
            prefix = context.prefix + context.command.full_parent_name + ' ' if context.command.full_parent_name else context.prefix
            add_single_command_field(embed, context.command, prefix=prefix)
            await context.send(embed=embed)

    async def get_context(self, message, *, cls=commands.Context):
        context = await super().get_context(message, cls=cls)
        new_command, alias, full_string = None, None, None
        # this is all pretty hacky tbh
        if context.prefix and isinstance(self.all_commands, CharTrie):
            no_prefix_content = message.content[len(context.prefix):]
            alias, new_command = self.all_commands.longest_prefix(no_prefix_content)
            full_string = context.prefix + alias if alias else None
        if isinstance(context.command, MemeGroup):
            group = context.command
            no_prefix_content = message.content[len(context.prefix):]
            no_group_content = no_prefix_content[len(group.qualified_name) + 1:]  # assume single space after group name
            alias, new_command = group.all_commands.longest_prefix(no_group_content)
            full_string = context.prefix + group.qualified_name + ' ' + alias if alias else None
        if new_command and alias and full_string:
            context.command = new_command
            context.invoked_with = alias
            context.view = StringView(message.content)
            context.view.skip_string(full_string)
        return context


def run():
    bot = MemeBot(command_prefix='!')
    bot.run(os.getenv('MEME_BOT_TOKEN'))


def run_debug():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--wait', action='store_true', default=False)
    args = parser.parse_args()

    log.debug(f'debug args: {args}')

    import ptvsd
    ptvsd.enable_attach()
    if args.wait:
        ptvsd.wait_for_attach()

    run()

if __name__ == "__main__":
    run()
