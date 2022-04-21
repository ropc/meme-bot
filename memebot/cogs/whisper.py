import asyncio
from distutils.command.config import config
import logging
import os.path
import discord
from dataclasses import dataclass
from typing import Optional, Dict, Callable, Awaitable, List
from pydantic import BaseModel
from discord.ext import commands


log = logging.getLogger('memebot')


EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

ReactionCallback = Callable[[discord.Reaction, discord.User], Awaitable[bool]]


class MemberConfig(BaseModel):
    member_id: int
    personal_channel_id: int
    whisper_count: Optional[int]


class GuildConfig(BaseModel):
    guild_id: int
    whisper_channel_id: Optional[int]
    member_configs: Dict[int, MemberConfig]
    role_id: int


class WhisperConfig(BaseModel):
    guild_configs: Dict[int, GuildConfig]

    class Config:
        arbitrary_types_allowed = True


def name_equals_ignore_case(name: str, member: discord.Member):
    name = name.lower()
    return (name == member.name.lower()
        or (member.nick and name == member.nick.lower()))


@dataclass
class MemberMatch:
    member: discord.Member
    is_high_confindence: bool

    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        '''note: this is only looking at cached members, so may not always work'''
        try:
            return cls(
                member=await commands.MemberConverter().convert(ctx, argument),
                is_high_confindence=True,
            )
        except commands.MemberNotFound:
            if not isinstance(argument, str):
                raise
            members = list(ctx.guild.members)
            matching_members = [member for member in members if name_equals_ignore_case(argument, member)]
            if len(matching_members) == 0:
                raise
            if len(matching_members) > 1:  # too ambiguous
                raise                      # maybe another interaction is possible?
            return cls(
                member=matching_members[0],
                is_high_confindence=ctx.guild.member_count == len(members),
            )


class Whisper(commands.Cog):
    def __init__(self, whisper_config_filepath: str):
        super().__init__()
        self.whisper_config_filepath = whisper_config_filepath
        self.whisper_config = self.load_or_create_default_config(whisper_config_filepath)
        self.callback_messages: Dict[int, ReactionCallback] = {}

    @commands.command()
    @commands.guild_only()
    async def whisper(self, context: commands.Context, member_match: MemberMatch, *, message: str):
        '''Send a whisper to another player.
        Name must be exact, put in quotes the name has a space.
        Examples: !whisper Jeff stop trolling
        !whisper "someone with a long name" lynch jeff
        '''
        guild_config = self.whisper_config.guild_configs.get(context.guild.id)
        if not guild_config:
            return

        sender = await get_member(context, context.author.id)
        if not sender:
            return await context.reply(f'unrecognized member')

        sender_config = guild_config.member_configs.get(sender.id)
        if not sender_config:
            return await context.reply(f'failed to send message. no config found for {context.author.mention}')

        if guild_config.role_id not in (role.id for role in sender.roles):
            return await context.reply('not allowed to whisper')

        if sender_config.whisper_count is not None and sender_config.whisper_count <= 0:
            return await context.reply('out of whispers')

        async def complete_whisper():
            receiver_config = guild_config.member_configs.get(member_match.member.id)
            if not receiver_config:
                return await context.reply(f'failed to send message. no config found for {member_match.member.mention}')

            receiver_channel = await get_channel(context, receiver_config.personal_channel_id)
            if not receiver_channel:
                return await context.reply(f'failed to send message. no personal channel found for {member_match.member.mention}')

            await receiver_channel.send(f'**{context.author.display_name} whispered you:** {message}')
            await context.message.add_reaction('📬')

            if sender_config.whisper_count is not None:
                sender_config.whisper_count -= 1
                self.save_config()
                await context.send(f'you have {sender_config.whisper_count} whisper(s) remaining')

            if not guild_config.whisper_channel_id:
                return

            whisper_list_channel = await get_channel(context, guild_config.whisper_channel_id)
            if not whisper_list_channel:
                return await context.send(f'unable to find whisper list channel id: {guild_config.whisper_channel_id}')
            await whisper_list_channel.send(f'{sender.display_name} whispered {member_match.member.display_name}')

        if not member_match.is_high_confindence:
            message = await context.reply(f'did you mean {member_match.member.mention}? (select below)')
            await message.add_reaction('👍')
            await message.add_reaction('👎')

            async def callback(reaction: discord.Reaction, user: discord.User):
                '''assumes react is for relevant message
                return value indicates whether or not this callback entry can be removed from self.callback_messages
                '''
                if user.id != context.author.id or reaction.emoji not in ('👍', '👎'):
                    return False

                if reaction.emoji == '👎':
                    await message.edit(content='please try again, name should be an EXACT match')
                    return True

                await complete_whisper()
                return True

            self.callback_messages[message.id] = callback
            return

        await complete_whisper()

    # manager commands

    @commands.command(aliases=['setup whispers', 'setup whisper'])
    @commands.has_role('whisper-manager')
    async def setup_server(self, context: commands.Context, category: discord.CategoryChannel,
            role: discord.Role, whisper_count_input: int, whisper_channel: Optional[discord.TextChannel]):
        '''Setup for whispers
        Usage: !setup whisper <channel category> <role> <whisper count> <optional: whisper channel>
        Example: !setup whisper "personal channels" @Player 2 #whisper-channel
        '''
        whisper_count = whisper_count_input if whisper_count_input >= 0 else None

        guild_config: GuildConfig = self.get_or_create_guild_config(
            force_create=True,
            guild_id=context.guild.id,
            whisper_channel_id=whisper_channel.id if whisper_channel else None,
            role_id=role.id
        )
        self.save_config()

        async def setup_personal_channel(channel: discord.TextChannel) -> Optional[ReactionCallback]:
            '''return true if done and no callback needed'''

            def set_member_personal_channel(member: discord.Member):
                guild_config.member_configs[member.id] = MemberConfig(
                    member_id=member.id,
                    personal_channel_id=channel.id,
                    whisper_count=whisper_count,
                )
                self.save_config()

            # possible members are those with individual permission overwrites
            # for the current channel
            possible_members: List[discord.Member] = [m for m in channel.members if not m.bot and not channel.overwrites_for(m).is_empty()]

            if len(possible_members) == 0:
                possible_members = [member for member in channel.members if not member.bot]

            if len(possible_members) == 0:
                await context.send(f'unable to find possible members for {channel.mention}')
                return

            if len(possible_members) > 1:  # annoying/over-engineered case
                options = list(zip(EMOJI_NUMBERS, possible_members))
                options_by_emoji = {x[0]: x[1] for x in options}
                options_text = '\n'.join(f'{emoji} - {member.mention}' for (emoji, member) in options)
                message: discord.Message = await context.send(f'Please select the corresponding user for {channel.mention}:\n{options_text}')

                # doing it this way so that they show up in order
                for (emoji, _) in options:
                    await message.add_reaction(emoji)

                async def callback(reaction: discord.Reaction, user: discord.User):
                    member = options_by_emoji.get(reaction.emoji)
                    if user.id != context.author.id or not member:
                        return False

                    set_member_personal_channel(member)
                    await message.edit(content=f'set personal channel for {member.mention} to {channel.mention}')
                    return True

                self.callback_messages[message.id] = callback
                return callback

            # only one member in possible_members
            # easy case/most likely case, no decision/input needed
            member = possible_members[0]
            set_member_personal_channel(member)
            await context.send(f'set personal channel for {member.mention} to {channel.mention}')

        with context.typing():
            await context.send(
                'Setting up server with the following:\n'
                + (f'whisper channel: **#{whisper_channel.name}**\n' if whisper_channel else '')
                + f'whisper role: **@{role.name}**\n'
                + f'starting whisper count: **{whisper_count if whisper_count else "∞"}**'
            )

            callbacks = await asyncio.gather(*[setup_personal_channel(channel) for channel in category.text_channels])

            if not any(callbacks):
                await context.send('done!')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        callback = self.callback_messages.get(reaction.message.id)
        if not callback:
            return

        can_delete = await callback(reaction, user)
        if can_delete:
            self.callback_messages.pop(reaction.message.id)

    @commands.command(aliases=['set player channel'])
    @commands.has_role('whisper-manager')
    async def set_personal_channel(self, context: commands.Context, member: discord.Member, channel: discord.TextChannel,
            role: discord.Role, whisper_channel: Optional[discord.TextChannel], whisper_count: Optional[int]):
        '''Set a single personal channel.
        Usage: !set player channel <user> <channel> <role> <optional: whisper list channel> <optional: whisper count>
        Example: !set player channel ro #ro @Player #whisper-list-channel 2
        '''
        guild_config: GuildConfig = self.get_or_create_guild_config(
            guild_id=context.guild.id,
            whisper_channel_id=whisper_channel.id if whisper_channel else None,
            role_id=role.id
        )
        guild_config.member_configs[member.id] = MemberConfig(
            member_id=member.id,
            personal_channel_id=channel.id,
            whisper_count=whisper_count,
        )
        self.save_config()
        await context.reply(f'set personal channel for {member.mention} to {channel.mention}')

    @commands.command(aliases=['set whisper channel'])
    @commands.has_role('whisper-manager')
    @commands.guild_only()
    async def set_whisper_channel(self, context: commands.Context, channel: discord.TextChannel):
        guild_config = self.whisper_config.guild_configs.get(context.guild.id)
        if not guild_config:
            return await context.reply('missing guild config. please setup with !setup server')

        guild_config.whisper_channel_id = channel.id
        self.save_config()

        await context.send(f'set whisper channel to {channel.mention}')

    @commands.command(aliases=['set whispers', 'set whisper count', 'swc'])
    @commands.has_role('whisper-manager')
    async def set_whisper_count(self, context: commands.Context, member: Optional[discord.Member], count: int):
        '''Set whisper count.
        Usage !set whispers <optional: single user> <count>
        Example: !set whispers 10
        For infinite whispers: !set whispers -1
        '''
        count_str = str(count) if count >= 0 else '∞'
        guild_config = self.whisper_config.guild_configs.get(context.guild.id)
        if not guild_config:
            return await context.reply('missing guild config')

        member_config = guild_config.member_configs.get(member.id) if member else None
        if member and member_config is None:
            return await context.reply(f'could not find config for member {member.mention}')

        async def set_and_notify_whisper_count(member_config: MemberConfig) -> Optional[discord.Member]:
            '''returns discord.Member if successful'''
            member = await get_member(context, member_config.member_id)
            if not member:
                await context.send(f'cound not find user with id {member_config.member_id}')
                return None

            if guild_config.role_id not in (role.id for role in member.roles):
                member_config.whisper_count = 0
                return None

            member_config.whisper_count = count if count >= 0 else None

            personal_channel = await get_channel(context, member_config.personal_channel_id)
            if not personal_channel:    
                await context.send(f'could not find personal channel for {member.mention if member else member_config.member_id}')
                return member

            await personal_channel.send(f'you now have {count_str} whisper(s)')
            return member

        with context.typing():
            member_configs = [member_config] if member_config else guild_config.member_configs.values()
            members = await asyncio.gather(*[set_and_notify_whisper_count(config) for config in member_configs])
            self.save_config()
            member_list_str = '\n'.join(member.display_name for member in members if member is not None)
            await context.reply(f"reset whisper count to {count_str} for:\n{member_list_str}")

    def load_or_create_default_config(self, whisper_config_filepath):
        if not os.path.isfile(whisper_config_filepath):
            return WhisperConfig(guild_configs={})
        try:
            config = WhisperConfig.parse_file(whisper_config_filepath)
            log.debug(f'loaded whisper config: {config}')
            return config
        except KeyError:
            raise
        except Exception:
            log.exception('failed to load config, using default')
            return WhisperConfig(guild_configs={})

    def save_config(self):
        with open(self.whisper_config_filepath, 'w+') as f:
            f.write(self.whisper_config.json())

    def get_or_create_guild_config(self, *, guild_id: int, whisper_channel_id: Optional[int], role_id: int, force_create=False) -> GuildConfig:
        guild_config = self.whisper_config.guild_configs.get(guild_id)
        if not guild_config or force_create:
            guild_config = GuildConfig(
                guild_id=guild_id,
                whisper_channel_id=whisper_channel_id,
                member_configs={},
                role_id=role_id,
            )
            self.whisper_config.guild_configs[guild_id] = guild_config
            self.save_config()
        return guild_config


async def get_channel(context: commands.Context, channel_id: int) -> Optional[discord.TextChannel]:
    return context.guild.get_channel(channel_id) or await context.guild.fetch_channel(channel_id)

async def get_member(context: commands.Context, member_id: int) -> Optional[discord.Member]:
    return context.guild.get_member(member_id) or await context.guild.fetch_member(member_id)
