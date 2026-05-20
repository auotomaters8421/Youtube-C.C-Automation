import requests
import time
import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from src.config import Config

async def update_inworld_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the Inworld API Key at runtime."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/update_inworld_key <key>`", parse_mode="Markdown")
        return
    new_value = context.args[0]
    Config.update_runtime_config("INWORLD_KEY", new_value)
    await update.message.reply_text(f"✅ *Inworld Key* updated to: `{new_value[:5]}...`", parse_mode="Markdown")

async def update_inworld_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the Inworld API Secret at runtime."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/update_inworld_secret <secret>`", parse_mode="Markdown")
        return
    new_value = context.args[0]
    Config.update_runtime_config("INWORLD_SECRET", new_value)
    await update.message.reply_text(f"✅ *Inworld Secret* updated to: `{new_value[:5]}...`", parse_mode="Markdown")

async def update_voice_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the Inworld Voice ID at runtime."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/update_voice_id <id>`", parse_mode="Markdown")
        return
    new_value = context.args[0]
    Config.update_runtime_config("INWORLD_VOICE_ID", new_value)
    await update.message.reply_text(f"✅ *Voice ID* updated to: `{new_value}`", parse_mode="Markdown")

async def update_deepgram_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the Deepgram API Key at runtime."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/update_deepgram_key <key>`", parse_mode="Markdown")
        return
    new_key = context.args[0]
    Config.update_runtime_config("DEEPGRAM_KEY", new_key)
    await update.message.reply_text("✅ *Deepgram API Key* updated for this session.", parse_mode="Markdown")

async def find_visuals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finds visual sources based on video script."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/find_visuals <video_id>`", parse_mode="Markdown")
        return
    
    video_id = context.args[0]
    await update.message.reply_text(f"🔍 Searching visual sources for {video_id}...")
    
    # 1. Locate the folder
    output_dir = Config.OUTPUT_DIR
    target_folder = None
    if os.path.exists(output_dir):
        for folder in os.listdir(output_dir):
            if folder.endswith(f"_{video_id}"):
                target_folder = os.path.join(output_dir, folder)
                break
                
    if not target_folder:
        await update.message.reply_text(f"❌ Error: Could not find output folder for {video_id}")
        return
        
    scripts_file = os.path.join(target_folder, "scripts.json")
    if not os.path.exists(scripts_file):
        await update.message.reply_text(f"❌ Error: scripts.json not found in {target_folder}")
        return
        
    import json
    import google.generativeai as genai
    try:
        with open(scripts_file, "r", encoding="utf-8") as f:
            scripts_data = json.load(f)
            
        script_text = scripts_data.get("standard_version", {}).get("body", "")
        if not script_text:
            script_text = str(scripts_data)
            
        # 2. Extract search query using Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Analyze the following script and extract the most relevant search query (just 2-5 words) to find the official blog post, official website, or visual sources for the AI tool or topic mentioned. Return ONLY the search query string, nothing else. Script: {script_text}"
        
        response = model.generate_content(prompt)
        query = response.text.strip()
        
        # 3. Search DuckDuckGo
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"[{r['title']}]({r['href']})")
                
        if results:
            reply_text = f"✅ *Visual Sources Found for '{query}':*\n\n" + "\n".join(results)
            await update.message.reply_text(reply_text, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await update.message.reply_text(f"❌ No sources found for query: `{query}`", parse_mode="Markdown")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error during search: {e}")

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
        "text": text
        # Removed parse_mode: Markdown to avoid errors on unescaped text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def send_file(file_path, caption=None):
    """
    Sends a file to the configured Telegram chat.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id or not os.path.exists(file_path):
        return

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            payload = {"chat_id": chat_id, "caption": caption}
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram file: {e}")

def send_audio(file_path, caption=None, title=None):
    """
    Sends an audio file to the configured Telegram chat.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id or not os.path.exists(file_path):
        return

    url = f"https://api.telegram.org/bot{token}/sendAudio"
    try:
        with open(file_path, "rb") as f:
            files = {"audio": f}
            payload = {
                "chat_id": chat_id, 
                "caption": caption,
                "title": title
            }
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram audio: {e}")

def send_approval_request(video):
    """
    Sends an approval request with Approve and Reject buttons for a specific video.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Telegram configuration missing.")
        return

    video_id = video.get('yt_videoid')
    title = video.get('title')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Dual button keyboard
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve|{video_id}"},
            {"text": "❌ Reject", "callback_data": f"reject|{video_id}"}
        ]]
    }
    
    text = (
        f"🎬 *New Top Recommendation*\n\n"
        f"*Title:* {title}\n"
        f"*Views:* {video.get('views', 0):,}\n"
        f"*Link:* [YouTube](https://youtube.com/watch?v={video_id})\n\n"
        f"Would you like to start production?"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram API Error {response.status_code}: {response.text}")
        response.raise_for_status()
        print(f"Sent approval request for: {title}")
    except Exception as e:
        print(f"Failed to send approval request: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries from inline buttons.
    """
    query = update.callback_query
    data = query.data
    
    import asyncio
    
    if data.startswith("approve|"):
        # 1. Answer immediately to stop spinner (Match spec: "🚀 Done! Production started.")
        await query.answer(text="🚀 Done! Production started.", show_alert=False)
        
        parts = data.split("|")
        if len(parts) >= 2:
            video_id = parts[1]
            
            # Extract actual title from the message to preserve it
            import re
            message_text = query.message.text
            video_title = video_id # Fallback
            title_match = re.search(r"Title:\s*(.*)", message_text)
            if title_match:
                video_title = title_match.group(1).strip()

            # 2. Update message to confirm approval (Match spec)
            await query.edit_message_text(
                text=f"✅ *Approved:* Starting Production for `{video_id}`..."
            )
            
            # 3. Offload blocking task to a thread
            from src.orchestrator import process_short_approval
            try:
                # Run in thread to keep bot responsive with actual title
                await asyncio.to_thread(process_short_approval, video_id, video_title)
            except Exception as e:
                import logging
                logging.error(f"Error during production for {video_id}: {e}")
                await query.edit_message_text(text=f"❌ *Production Error:* {str(e)}")
                
    elif data.startswith("reject|"):
        # 1. Answer immediately
        await query.answer(text="❌ Recommendation Discarded.", show_alert=False)
        
        # 2. Update message to confirm rejection
        await query.edit_message_text(text="🗑️ *Recommendation Discarded.*")

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
    # Disable JobQueue if it's causing weakref issues in Python 3.13
    application = Application.builder().token(token).job_queue(None).build()
    
    # Add handler for button callbacks (Approve/Reject)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add handlers for runtime config updates
    application.add_handler(CommandHandler("update_inworld_key", update_inworld_key))
    application.add_handler(CommandHandler("update_inworld_secret", update_inworld_secret))
    application.add_handler(CommandHandler("update_voice_id", update_voice_id))
    application.add_handler(CommandHandler("update_deepgram_key", update_deepgram_key))
    application.add_handler(CommandHandler("find_visuals", find_visuals))
    
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
