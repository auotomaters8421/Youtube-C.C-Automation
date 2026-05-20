import os
import logging
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Config:
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    INWORLD_KEY: Optional[str] = os.getenv("INWORLD_KEY")
    INWORLD_SECRET: Optional[str] = os.getenv("INWORLD_SECRET")
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    DEEPGRAM_KEY: Optional[str] = os.getenv("DEEPGRAM_KEY")
    CHANNELS: List[str] = os.getenv("CHANNELS", "").split(",") if os.getenv("CHANNELS") else []
    OUTPUT_DIR: str = "output"

    # Shorts Reframer Config
    INWORLD_VOICE_ID: str = os.getenv("INWORLD_VOICE_ID", "default-d010pwu587xlzwrg_tencw__coyied_voice")
    INWORLD_FALLBACK_VOICE: str = os.getenv("INWORLD_FALLBACK_VOICE", "Alex")
    
    # Persistence Config
    MONGO_URI: Optional[str] = os.getenv("MONGO_URI")
    SEEN_VIDEOS_PATH: str = os.getenv("SEEN_VIDEOS_PATH", os.path.join("data", "seen_videos.json"))
    
    @classmethod
    def update_runtime_config(cls, key: str, value: str):
        """Updates configuration at runtime."""
        if hasattr(cls, key):
            setattr(cls, key, value)
            logging.info(f"Runtime config updated: {key} is now set.")
            return True
        return False

    @classmethod
    def get_gemini_system_prompt(cls) -> str:
        """Loads the Gemini system prompt from the specs directory."""
        prompt_path = os.path.join("docs", "superpowers", "specs", "Systemprompt.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logging.error(f"System prompt file not found at {prompt_path}")
            return "Reframe the following YouTube Short transcript into a viral and standard version."

    @classmethod
    def validate(cls):
        """
        Validates that all mandatory configuration keys are present.
        """
        mandatory_keys = [
            "GEMINI_API_KEY",
            "INWORLD_KEY",
            "INWORLD_SECRET",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "DEEPGRAM_KEY"
        ]
        missing = [key for key in mandatory_keys if not getattr(cls, key)]
        if missing:
            logging.warning(f"Missing mandatory configuration keys: {', '.join(missing)}")

    @classmethod
    def add_channel(cls, channel_id: str) -> bool:
        """
        Permanently adds a channel ID to runtime config and updates the .env file.
        """
        if channel_id not in cls.CHANNELS:
            cls.CHANNELS.append(channel_id)
            env_path = ".env"
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    channels_line_idx = -1
                    for idx, line in enumerate(lines):
                        if line.strip().startswith("CHANNELS="):
                            channels_line_idx = idx
                            break
                    if channels_line_idx != -1:
                        curr_line = lines[channels_line_idx].strip()
                        curr_val = curr_line.split("=", 1)[1].strip("\"'")
                        if curr_val:
                            new_val = f"{curr_val},{channel_id}"
                        else:
                            new_val = channel_id
                        lines[channels_line_idx] = f'CHANNELS="{new_val}"\n'
                    else:
                        lines.append(f'\nCHANNELS="{channel_id}"\n')
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                except Exception as e:
                    logging.error(f"Failed to persist channel to .env: {e}")
            return True
        return False

