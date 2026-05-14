import requests
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from src.config import Config

def send_message(text):
    """
    Sends a simple text message to the configured Telegram chat.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Telegram configuration missing.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def send_approval_request(video):
    """
    Sends an approval request with a 'GO' button for a specific video.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Telegram configuration missing.")
        return

    video_id = video.get('yt_videoid')
    title = video.get('title')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Inline keyboard markup using raw dict for requests
    keyboard = {
        "inline_keyboard": [[
            {"text": "🚀 GO", "callback_data": f"go|{video_id}|{title}"}
        ]]
    }
    
    text = (
        f"🎬 *New Top Recommendation*\n\n"
        f"*Title:* {title}\n"
        f"*Views:* {video.get('views', 0):,}\n"
        f"*Link:* [YouTube](https://youtube.com/watch?v={video_id})\n\n"
        f"Click the button below to start production."
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Sent approval request for: {title}")
    except Exception as e:
        print(f"Failed to send approval request: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries from inline buttons.
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("go|"):
        parts = data.split("|")
        if len(parts) >= 3:
            video_id = parts[1]
            title = "|".join(parts[2:]) # Handle titles that might contain |
            
            await query.edit_message_text(text=f"⏳ *Production Started:* {title}\n(Reframing and generating assets...)")
            
            # Import here to avoid circular dependency
            from src.orchestrator import process_short_approval
            # Run production
            try:
                # We call it directly. For long running tasks in a real bot, 
                # this would ideally be offloaded to a worker thread.
                process_short_approval(video_id, title)
            except Exception as e:
                print(f"Error during production: {e}")
                await query.edit_message_text(text=f"❌ *Error producing:* {title}\nCheck logs for details.")

def start_bot(run=True):
    """
    Starts the Telegram bot to listen for approval clicks.
    If run=True, it blocks and runs the bot (run_polling).
    If run=False, it initializes and returns the application.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        print("TELEGRAM_BOT_TOKEN not configured.")
        return None

    print("Initializing Telegram bot...")
    application = Application.builder().token(token).build()
    
    # Add handler for the 'GO' button
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    if run:
        print("Bot is running. Waiting for user approval...")
        # This will block until the process is stopped
        application.run_polling(drop_pending_updates=True)
    else:
        # Initialize and start but return for main thread to manage
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.updater.start_polling())
        loop.run_until_complete(application.start())
        return application

def wait_for_approval(timeout=60, poll_interval=5):
    """
    Old polling method - deprecated in favor of start_bot().
    Kept for backward compatibility if needed.
    """
    print("Warning: wait_for_approval is deprecated. Use start_bot().")
    return False
