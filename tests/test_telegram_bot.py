import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.telegram_bot import update_deepgram_key, update_gemini_key, list_keys
from src.config import Config

@pytest.mark.asyncio
async def test_update_deepgram_key_success():
    # Setup
    update = MagicMock()
    update.message = AsyncMock()
    context = MagicMock()
    context.args = ["new_test_key"]
    
    # Execute
    with patch.object(Config, "update_runtime_config") as mock_update:
        await update_deepgram_key(update, context)
        
        # Verify
        mock_update.assert_called_once_with("DEEPGRAM_KEY", "new_test_key")
        update.message.reply_text.assert_called_once()
        assert "✅" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_update_deepgram_key_no_args():
    # Setup
    update = MagicMock()
    update.message = AsyncMock()
    context = MagicMock()
    context.args = []
    
    # Execute
    await update_deepgram_key(update, context)
    
    # Verify
    update.message.reply_text.assert_called_once()
    assert "Usage" in update.message.reply_text.call_args[0][0]

def test_start_bot_registers_handler():
    from src.telegram_bot import start_bot
    from telegram.ext import CommandHandler
    
    with patch("src.telegram_bot.Application") as mock_app_class:
        mock_app = MagicMock()
        mock_app_class.builder().token().job_queue().build.return_value = mock_app
        
        # Call start_bot with run=False to avoid polling
        # But wait, start_bot(run=False) tries to initialize and start polling using asyncio
        # I should probably just mock the whole thing or test the registration logic
        
        with patch("src.telegram_bot.Config") as mock_config:
            mock_config.TELEGRAM_BOT_TOKEN = "test_token"
            
            # Mock the asyncio parts in start_bot(run=False)
            with patch("asyncio.get_event_loop") as mock_loop:
                start_bot(run=False)
                
                # Verify that add_handler was called with update_deepgram_key
                # We need to find the call that added update_deepgram_key CommandHandler
                found = False
                for call in mock_app.add_handler.call_args_list:
                    handler = call[0][0]
                    if isinstance(handler, CommandHandler) and "update_deepgram_key" in handler.commands:
                        found = True
                        break
                assert found, "update_deepgram_key handler not registered"


def test_fetch_video_title_scenarios():
    from src.telegram_bot import fetch_video_title
    
    # 1. Test standard successful case
    with patch("src.telegram_bot.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<html><head><title>Awesome AI Tutorial - YouTube</title></head></html>'
        mock_get.return_value = mock_response
        
        title = fetch_video_title("xyz12345678")
        assert title == "Awesome AI Tutorial"
        
    # 2. Test deleted/private video case (only suffix is returned by YouTube)
    with patch("src.telegram_bot.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<html><head><title> - YouTube</title></head></html>'
        mock_get.return_value = mock_response
        
        title = fetch_video_title("xyz12345678")
        assert title == "YouTube Video xyz12345678"

    # 3. Test empty title tag case
    with patch("src.telegram_bot.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<html><head><title></title></head></html>'
        mock_get.return_value = mock_response
        
        title = fetch_video_title("xyz12345678")
        assert title == "YouTube Video xyz12345678"


@pytest.mark.asyncio
async def test_update_gemini_key_success():
    """Test /update_gemini_key updates Config and reconfigures genai SDK."""
    update = MagicMock()
    update.message = AsyncMock()
    context = MagicMock()
    context.args = ["AIzaSy_new_test_key"]

    with patch.object(Config, "update_runtime_config") as mock_update, \
         patch.dict('sys.modules', {'google.generativeai': MagicMock()}):
        await update_gemini_key(update, context)

        mock_update.assert_called_once_with("GEMINI_API_KEY", "AIzaSy_new_test_key")
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "✅" in call_text

@pytest.mark.asyncio
async def test_update_gemini_key_no_args():
    """Test /update_gemini_key shows usage when no key provided."""
    update = MagicMock()
    update.message = AsyncMock()
    context = MagicMock()
    context.args = []

    await update_gemini_key(update, context)

    update.message.reply_text.assert_called_once()
    assert "Usage" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_list_keys_shows_all_platforms():
    """Test /list_keys shows status for all major platform keys."""
    update = MagicMock()
    update.message = AsyncMock()
    context = MagicMock()

    original_gemini = Config.GEMINI_API_KEY
    original_deepgram = Config.DEEPGRAM_KEY
    try:
        Config.GEMINI_API_KEY = "AIzaSyTestKey12345"
        Config.DEEPGRAM_KEY = None

        await list_keys(update, context)

        call_text = update.message.reply_text.call_args[0][0]
        assert "API Key Status Dashboard" in call_text
        assert "Gemini API Key" in call_text
        assert "Inworld Key" in call_text
        assert "Deepgram Key" in call_text
    finally:
        Config.GEMINI_API_KEY = original_gemini
        Config.DEEPGRAM_KEY = original_deepgram

def test_start_bot_registers_new_commands():
    """Verify that update_gemini_key and list_keys handlers are registered."""
    from src.telegram_bot import start_bot
    from telegram.ext import CommandHandler

    with patch("src.telegram_bot.Application") as mock_app_class:
        mock_app = MagicMock()
        mock_app_class.builder().token().job_queue().build.return_value = mock_app

        with patch("src.telegram_bot.Config") as mock_config:
            mock_config.TELEGRAM_BOT_TOKEN = "test_token"

            with patch("asyncio.get_event_loop") as mock_loop:
                start_bot(run=False)

                registered_commands = set()
                for call in mock_app.add_handler.call_args_list:
                    handler = call[0][0]
                    if isinstance(handler, CommandHandler):
                        registered_commands.update(handler.commands)

                assert "update_gemini_key" in registered_commands, "update_gemini_key handler not registered"
                assert "list_keys" in registered_commands, "list_keys handler not registered"
                assert "update_deepgram_key" in registered_commands
                assert "update_inworld_key" in registered_commands

def test_resolve_video_id():
    from src.telegram_bot import resolve_video_id
    from src.config import Config
    
    # Mock seen videos path or list to avoid real JSON/Mongo dependency
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open") as mock_open:
        
        # Mock JSON loader to return a few sample video IDs
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = '["M2DzY0c9rjI", "FuCYqz3Dokk", "abcde12345O"]'
        mock_open.return_value = mock_file
        
        # 1. Test exact match
        assert resolve_video_id("M2DzY0c9rjI") == "M2DzY0c9rjI"
        
        # 2. Test case-insensitive match
        assert resolve_video_id("m2dzy0c9rji") == "M2DzY0c9rjI"
        
        # 3. Test visual homoglyphs match ('l' confuses with 'I')
        # M2DzY0c9rjl ends in lowercase 'l', should resolve to 'M2DzY0c9rjI'
        assert resolve_video_id("M2DzY0c9rjl") == "M2DzY0c9rjI"
        
        # 4. Test visual homoglyphs match ('o' vs 'O')
        assert resolve_video_id("abcde12345o") == "abcde12345O"
        
        # 5. Test unknown ID remains original
        assert resolve_video_id("unknownID12") == "unknownID12"

