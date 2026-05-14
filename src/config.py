import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Config:
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    INWORLD_KEY: Optional[str] = os.getenv("INWORLD_KEY")
    INWORLD_SECRET: Optional[str] = os.getenv("INWORLD_SECRET")
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    CHANNELS: List[str] = os.getenv("YOUTUBE_CHANNELS", "").split(",") if os.getenv("YOUTUBE_CHANNELS") else []
    OUTPUT_DIR: str = "output"

    # Shorts Reframer Config
    INWORLD_VOICE_ID: str = os.getenv("INWORLD_VOICE_ID", "default-d010pwu587xlzwrg_tencw__my_voice")
    INWORLD_FALLBACK_VOICE: str = os.getenv("INWORLD_FALLBACK_VOICE", "Alex")
    GEMINI_SYSTEM_PROMPT: str = os.getenv("GEMINI_SYSTEM_PROMPT", "Reframe the following YouTube Short transcript into a controversial, problem-solving script. Focus on a heavy hook in the first 3 seconds.")

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
            "TELEGRAM_CHAT_ID"
        ]
        missing = [key for key in mandatory_keys if not getattr(cls, key)]
        if missing:
            import logging
            logging.warning(f"Missing mandatory configuration keys: {', '.join(missing)}")
