import json
import discord
from pydantic import BaseModel
from typing import Dict, Optional


class GuildConfig(BaseModel):
    voice_channel: str
    text_channel: str


class Config(BaseModel):
    config_file: str

    def get_guild_config(self, guild_id: int) -> Optional[GuildConfig]:
        with open(self.config_file) as f:
            config = json.load(f)
            guild_config_dict: Dict = config.get('guild_configs', {}).get(str(guild_id), {})
            voice_channel = guild_config_dict.get('bot_voice_channel')
            text_channel = guild_config_dict.get('bot_text_channel')
            if voice_channel and text_channel:
                return GuildConfig(voice_channel=voice_channel, text_channel=text_channel)
        return None
