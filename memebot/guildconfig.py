import json
from typing import Optional, Dict
from pydantic import BaseModel


class GuildConfig(BaseModel):
    voice_channel_id: int
    text_channel_id: int


MemeBotConfig = Dict[int, GuildConfig]


def get_guild_config(guild_config_dict) -> Optional[GuildConfig]:
    voice_channel = guild_config_dict.get('bot_voice_channel')
    text_channel = guild_config_dict.get('bot_text_channel')
    if voice_channel and text_channel:
        return GuildConfig(voice_channel_id=voice_channel, text_channel_id=text_channel)
    return None

def get_guild_config_dict(config_string: str) -> MemeBotConfig:
    config = json.loads(config_string)
    guild_configs = config.get('guild_configs', {})
    return {int(gid): guild_config for (gid, config_dict) in guild_configs.items() if (guild_config := get_guild_config(config_dict))}
