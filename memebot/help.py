# Modified from https://gist.github.com/Rapptz/31a346ed1eb545ddeb0d451d81a60b3b
import discord
from discord.ext import commands
from typing import Union


class EmbedHelpCommand(commands.HelpCommand):
    """This is an example of a HelpCommand that utilizes embeds.
    It's pretty basic but it lacks some nuances that people might expect.
    1. It breaks if you have more than 25 cogs or more than 25 subcommands. (Most people don't reach this)
    2. It doesn't DM users. To do this, you have to override `get_destination`. It's simple.
    Other than those two things this is a basic skeleton to get you started. It should
    be simple to modify if you desire some other behaviour.
    
    To use this, pass it to the bot constructor e.g.:
       
    bot = commands.Bot(help_command=EmbedHelpCommand())
    """

    def get_ending_note(self):
        return 'Use {0}{1} [command] for more info on a command.'.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command: commands.Command):
        return f'{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Commands')
        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, command_list in mapping.items():
            filtered_commands = await self.filter_commands(command_list, sort=True)
            for command in filtered_commands:
                await self._recursive_add_command_field(embed, command)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog))
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: Union[commands.Command, commands.Group]):
        embed = discord.Embed(title=group.qualified_name)
        if group.help:
            embed.description = group.help

        await self._recursive_add_command_field(embed, group)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    # This makes it so it uses the function above
    # Less work for us to do since they're both similar.
    # If you want to make regular command help look different then override it
    send_command_help = send_group_help

    async def _recursive_add_command_field(self, embed: discord.Embed, command: Union[commands.Command, commands.Group], prefix=''):
        if not isinstance(command, commands.Group):
            _add_single_command_field(embed, command, prefix=prefix)
            return
        _add_single_command_field(embed, command, prefix=prefix)
        filtered_commands = await self.filter_commands(command.commands)
        for subcommand in filtered_commands:
            await self._recursive_add_command_field(embed, subcommand, prefix=command.qualified_name + ' ')


def _add_single_command_field(embed: discord.Embed, command: commands.Command, prefix=''):
    name = ', '.join(f'**{prefix}{a}**' for a in command.aliases) if command.aliases else command.qualified_name
    value = '\n'.join(line.strip() for line in command.short_doc.splitlines())
    embed.add_field(name=name, value=value, inline=False)
