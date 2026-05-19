import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.telegram_bot import update_deepgram_key
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
