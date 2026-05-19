import os
import importlib
import pytest
from unittest.mock import patch
import src.config

def test_config_loads_variables(monkeypatch):
    with patch("src.config.load_dotenv"):
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
        monkeypatch.setenv("INWORLD_KEY", "test_inworld_key")
        monkeypatch.setenv("INWORLD_SECRET", "test_inworld_secret")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_id")
        monkeypatch.setenv("DEEPGRAM_KEY", "test_deepgram_key")
        monkeypatch.setenv("CHANNELS", "chan1,chan2")

        # Reload the config module to pick up the monkeypatched environment variables
        importlib.reload(src.config)
        from src.config import Config

        assert Config.GEMINI_API_KEY == "test_gemini_key"
        assert Config.INWORLD_KEY == "test_inworld_key"
        assert Config.INWORLD_SECRET == "test_inworld_secret"
        assert Config.TELEGRAM_BOT_TOKEN == "test_bot_token"
        assert Config.TELEGRAM_CHAT_ID == "test_chat_id"
        assert Config.DEEPGRAM_KEY == "test_deepgram_key"
        assert Config.CHANNELS == ["chan1", "chan2"]
        assert Config.OUTPUT_DIR == "output"

def test_config_default_channels(monkeypatch):
    with patch("src.config.load_dotenv"):
        monkeypatch.setenv("CHANNELS", "")
        importlib.reload(src.config)
        from src.config import Config
        assert Config.CHANNELS == []

def test_config_validate_missing_key(monkeypatch):
    # Mock os.getenv to return None for DEEPGRAM_KEY
    def mock_getenv(key, default=None):
        env = {
            "GEMINI_API_KEY": "test",
            "INWORLD_KEY": "test",
            "INWORLD_SECRET": "test",
            "TELEGRAM_BOT_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test"
        }
        return env.get(key, default)

    with patch("os.getenv", side_effect=mock_getenv):
        with patch("src.config.load_dotenv"):
            importlib.reload(src.config)
            from src.config import Config
            
            assert Config.DEEPGRAM_KEY is None
            
            with patch("src.config.logging.warning") as mock_warning:
                Config.validate()
                assert mock_warning.called
