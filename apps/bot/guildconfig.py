import json
from typing import Optional, Dict
from pydantic import BaseModel


class GuildConfig(BaseModel):
    voice_channel_id: int
    text_channel_id: int

def get_guild_config(config_string: str, guild_id: int) -> Optional[GuildConfig]:
    config = json.loads(config_string)
    guild_config_dict: Dict = config.get('guild_configs', {}).get(str(guild_id), {})
    voice_channel = guild_config_dict.get('bot_voice_channel')
    text_channel = guild_config_dict.get('bot_text_channel')
    if voice_channel and text_channel:
        return GuildConfig(voice_channel_id=voice_channel, text_channel_id=text_channel)
    return None
