import asyncio
import logging
import os.path
import discord
from dataclasses import dataclass
from typing import Optional, Dict, Union
from pydantic import BaseModel
from discord.ext import commands


log = logging.getLogger('memebot')


EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']


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


@dataclass
class PersonalChannelConfigOptions:
    member_options: Dict[str, discord.Member]  # emoji to discord.Member
    channel: discord.TextChannel
    whisper_count: Optional[int]
    initiator: discord.Member
    guild_id: int
    role_id: int


class Whisper(commands.Cog):
    def __init__(self, whisper_config_filepath: str):
        super().__init__()
        self.whisper_config_filepath = whisper_config_filepath
        self.whisper_config = self.load_or_create_default_config(whisper_config_filepath)
        self.decision_messages: Dict[int, PersonalChannelConfigOptions] = {}

    @commands.command()
    @commands.guild_only()
    async def whisper(self, context: commands.Context, receiver: discord.Member, *, message: str):
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

        receiver_config = guild_config.member_configs.get(receiver.id)
        if not receiver_config:
            return await context.reply(f'failed to send message. no config found for {receiver.mention}')

        receiver_channel = await get_channel(context, receiver_config.personal_channel_id)
        if not receiver_channel:
            return await context.reply(f'failed to send message. no personal channel found for {receiver.mention}')

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
        await whisper_list_channel.send(f'{sender.display_name} whispered {receiver.display_name}')

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
        with context.typing():
            guild_config: GuildConfig = self.get_or_create_guild_config(
                force_create=True,
                guild_id=context.guild.id,
                whisper_channel_id=whisper_channel.id if whisper_channel else None,
                role_id=role.id
            )
            self.save_config()

            await context.send(
                'Setting up server with the following:\n'
                + (f'whisper channel: **#{whisper_channel.name}**\n' if whisper_channel else '')
                + f'whisper role: **@{role.name}**\n'
                + f'starting whisper count: **{whisper_count if whisper_count else "∞"}**'
            )

            decision_messages = {}
            for channel in category.text_channels:
                # possible members are those with individual permission overwrites
                # for the current channel
                possible_members = []
                for member in channel.members:
                    if member.bot:
                        continue
                    permissions_overwrite = channel.overwrites_for(member)
                    if permissions_overwrite.is_empty():
                        continue
                    possible_members.append(member)

                if len(possible_members) == 0:
                    possible_members = [member for member in channel.members if not member.bot]

                if len(possible_members) == 0:
                    await context.send(f'unable to find possible members for {channel.mention}')
                    continue

                # easy case, no decision/input needed
                if len(possible_members) == 1:
                    member = possible_members[0]
                    guild_config.member_configs[member.id] = MemberConfig(
                        member_id=member.id,
                        personal_channel_id=channel.id,
                        whisper_count=whisper_count,
                    )
                    self.save_config()
                    await context.send(f'set personal channel for {member.mention} to {channel.mention}')
                    continue

                options = list(zip(EMOJI_NUMBERS, possible_members))
                options_text = '\n'.join(f'{emoji} - {member.mention}' for (emoji, member) in options)
                message = await context.send(f'Please select the corresponding user for {channel.mention}:\n{options_text}')

                # doing it this way so that they show up in order
                for (emoji, _) in options:
                    await message.add_reaction(emoji)

                decision_messages[message.id] = PersonalChannelConfigOptions(
                    member_options={option[0]: option[1] for option in options},
                    channel=channel,
                    whisper_count=whisper_count,
                    initiator=context.author,
                    role_id=role.id,
                    guild_id=context.guild.id,
                )

            self.decision_messages = decision_messages

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        options = self.decision_messages.get(reaction.message.id)
        if not options or options.initiator.id != user.id:
            # options is missing or someone else reacted
            return

        selected_member = options.member_options.get(reaction.emoji)
        if not selected_member:
            # added some other emoji that wasn't an option
            return

        guild_config = self.whisper_config.guild_configs.get(reaction.message.guild.id)
        guild_config.member_configs[selected_member.id] = MemberConfig(
            member_id=selected_member.id,
            personal_channel_id=options.channel.id,
            whisper_count=options.whisper_count,
        )
        self.save_config()
        self.decision_messages.pop(reaction.message.id)

        await reaction.message.edit(content=f'set personal channel for {selected_member.mention} to {options.channel.mention}')

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

    @commands.command(aliases=['set whispers', 'set whisper count', 'swc'])
    @commands.has_role('whisper-manager')
    async def set_whisper_count(self, context: commands.Context, count: int, member: Optional[discord.Member]):
        '''Set whisper count.
        Usage !set whispers <count> <optional: single user>
        Example: !set whispers 10
        For infinite whispers: !set whispers -1
        '''
        count_str = str(count) if count >= 0 else '∞'
        guild_config = self.whisper_config.guild_configs.get(context.guild.id)
        if not guild_config:
            await context.reply('missing guild config')
            return

        async def set_and_notify_whisper_count(member_config: MemberConfig):
            member = await get_member(context, member_config.member_id)
            if not member:
                return await context.send(f'cound not find user with id {member_config.member_id}')

            if guild_config.role_id not in (role.id for role in member.roles):
                member_config.whisper_count = 0
                return

            member_config.whisper_count = count if count >= 0 else None

            personal_channel = await get_channel(context, member_config.personal_channel_id)
            if not personal_channel:    
                return await context.send(f'could not find personal channel for {member.mention if member else member_config.member_id}')

            return await personal_channel.send(f'you now have {count_str} whisper(s)')

        with context.typing():
            members = guild_config.member_configs.values() if not member else [member]
            await asyncio.gather(*[set_and_notify_whisper_count(config) for config in members])
            self.save_config()
            await context.reply(f"reset everyone's whisper count to {count_str}")

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