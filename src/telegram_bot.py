import requests
import time
import os
import asyncio
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
from src.config import Config

def extract_video_id(url: str) -> str:
    """
    Extracts the 11-character video ID from any YouTube URL.
    """
    patterns = [
        r"(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    cleaned = url.strip()
    if len(cleaned) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", cleaned):
        return cleaned
    return None

def fetch_video_title(video_id: str) -> str:
    """
    Fetches the video title via scraping.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        # Try og:title
        m = re.search(r'<meta property="og:title" content="([^"]+)">', r.text)
        if m:
            title = m.group(1)
            if title.endswith(" - YouTube"):
                title = title[:-10]
            return title
        # Try name="title"
        m = re.search(r'<meta name="title" content="([^"]+)">', r.text)
        if m:
            return m.group(1)
        # Try title tag
        m = re.search(r'<title>(.*?)</title>', r.text)
        if m:
            title = m.group(1)
            if title.endswith(" - YouTube"):
                title = title[:-10]
            return title
    except Exception as e:
        print(f"Error fetching title for {video_id}: {e}")
    return f"YouTube Video {video_id}"


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
        model = genai.GenerativeModel(Config.GEMINI_FLASH_MODEL)
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

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a new channel ID to search feeds for."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/add_channel <channel_id>`", parse_mode="Markdown")
        return
    channel_id = context.args[0].strip()
    if Config.add_channel(channel_id):
        await update.message.reply_text(f"✅ Channel `{channel_id}` has been successfully added and saved.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"ℹ️ Channel `{channel_id}` is already in the list.", parse_mode="Markdown")

async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually processes a YouTube URL, with optional visual sources search."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/process_url <youtube_url> [yes/no]`", parse_mode="Markdown")
        return
    
    url = context.args[0].strip()
    include_sources = False
    
    # Parse optional argument [yes/no]
    if len(context.args) > 1:
        sources_arg = context.args[1].lower().strip()
        if sources_arg in ["yes", "sources", "true", "y"]:
            include_sources = True
            
    video_id = extract_video_id(url)
    if not video_id:
        await update.message.reply_text("❌ Invalid YouTube URL or video ID. Please ensure it contains a valid 11-character video ID.")
        return
        
    await update.message.reply_text(f"📥 Fetching details for video ID `{video_id}`...")
    
    def run_production():
        try:
            # Fetch title
            title = fetch_video_title(video_id)
            # Notify
            send_message(f"🚀 Started manual production for: {title} (ID: {video_id}, include_sources={include_sources})")
            # Run orchestrator process_short_approval
            from src.orchestrator import process_short_approval
            process_short_approval(video_id, title, include_sources=include_sources)
        except Exception as e:
            import logging
            logging.error(f"Error in manual production for {video_id}: {e}")
            send_message(f"❌ Error in manual production for {video_id}: {e}")
        
    # Start execution in thread
    import threading
    thread = threading.Thread(target=run_production)
    thread.start()

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
    Sends an approval request with a Tag for tagging-based approval.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Telegram configuration missing.")
        return

    video_id = video.get('yt_videoid')
    title = video.get('title')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    tag = f"#video_{video_id}"
    
    text = (
        f"🎬 *New Top Recommendation*\n\n"
        f"*Title:* {title}\n"
        f"*Views:* {video.get('views', 0):,}\n"
        f"*Link:* [YouTube](https://youtube.com/watch?v={video_id})\n\n"
        f"🏷️ *Tag:* `{tag}`\n\n"
        f"To start production:\n"
        f"1. *Reply* to this message with `approve` or `reject`\n"
        f"2. Or *type* `{tag} approve` anywhere in the chat."
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
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

async def handle_text_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles plain text messages sent to the bot:
    1. YouTube URLs directly pasted -> Inspiration Mode (Auto-Cloning).
    2. Replies to bot recommendation messages with "approve"/"reject".
    3. Explicit "#video_ID approve" patterns typed directly.
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    
    # --- 1. Detect Direct YouTube / Shorts URLs (Inspiration mode) ---
    video_id = extract_video_id(text)
    if video_id:
        title = fetch_video_title(video_id)
        await update.message.reply_text(
            f"🎯 *Inspiration Mode Detected!*\n\n"
            f"*Original Title:* {title}\n"
            f"Fetching transcript and preparing upgraded copy with different psychological hooks...",
            parse_mode="Markdown"
        )
        
        # Offload cloning to thread to keep bot fully responsive
        from src.orchestrator import process_inspiration_url
        import threading
        thread = threading.Thread(target=process_inspiration_url, args=(video_id, title))
        thread.start()
        return

    # --- 2. Detect Reply-Based Approvals ---
    if update.message.reply_to_message and update.message.reply_to_message.text:
        parent_text = update.message.reply_to_message.text
        
        # 2A. Reply to automatic feed recommendation
        match = re.search(r"#video_([a-zA-Z0-9_-]{11})", parent_text)
        if match:
            video_id = match.group(1)
            action = text.lower()
            
            # Fetch video title from parent message
            video_title = video_id
            title_match = re.search(r"Title:\s*(.*)", parent_text)
            if title_match:
                video_title = title_match.group(1).strip()
                
            if "approve" in action:
                await update.message.reply_text(
                    f"✅ *Tag Approved via Reply!*\nStarting Production for video `{video_id}`...",
                    parse_mode="Markdown"
                )
                from src.orchestrator import process_short_approval
                import threading
                thread = threading.Thread(target=process_short_approval, args=(video_id, video_title))
                thread.start()
                return
            elif "reject" in action:
                await update.message.reply_text(
                    f"🗑️ *Tag Rejected via Reply.*\nDiscarded recommendation: `{video_title}`",
                    parse_mode="Markdown"
                )
                return

        # 2B. Reply to inspiration draft review
        insp_match = re.search(r"#insp_approve_([a-zA-Z0-9_-]{11})", parent_text)
        if insp_match:
            video_id = insp_match.group(1)
            action = text.lower()
            
            if "approve" in action:
                await update.message.reply_text(
                    f"✅ *Inspiration Script Approved via Reply!*\nGenerating TTS voice audio for video `{video_id}`...",
                    parse_mode="Markdown"
                )
                from src.orchestrator import process_inspiration_approval
                import threading
                thread = threading.Thread(target=process_inspiration_approval, args=(video_id,))
                thread.start()
                return
            elif "reject" in action:
                await update.message.reply_text(
                    f"🗑️ *Inspiration Script Rejected via Reply.*\nDiscarded copy for video ID `{video_id}`.",
                    parse_mode="Markdown"
                )
                return

    # --- 3. Detect Explicit Hashtag Approval Patterns ---
    
    # 3A. Explicit automatic recommendation approval (#video_XXXX approve)
    hashtag_match = re.search(r"#video_([a-zA-Z0-9_-]{11})\s+(approve|reject)", text, re.IGNORECASE)
    if hashtag_match:
        video_id = hashtag_match.group(1)
        action = hashtag_match.group(2).lower()
        video_title = fetch_video_title(video_id)
        
        if action == "approve":
            await update.message.reply_text(
                f"✅ *Tag Approved via Explicit Tag!*\nStarting Production for video `{video_id}`...",
                parse_mode="Markdown"
            )
            from src.orchestrator import process_short_approval
            import threading
            thread = threading.Thread(target=process_short_approval, args=(video_id, video_title))
            thread.start()
        else:
            await update.message.reply_text(
                f"🗑️ *Tag Rejected via Explicit Tag.*\nDiscarded recommendation: `{video_title}`",
                parse_mode="Markdown"
            )
        return

    # 3B. Explicit inspiration approval (#insp_approve_XXXX approve)
    insp_hashtag_match = re.search(r"#insp_approve_([a-zA-Z0-9_-]{11})\s+(approve|reject)", text, re.IGNORECASE)
    if insp_hashtag_match:
        video_id = insp_hashtag_match.group(1)
        action = insp_hashtag_match.group(2).lower()
        
        if action == "approve":
            await update.message.reply_text(
                f"✅ *Inspiration Script Approved via Explicit Tag!*\nGenerating TTS voice audio for video `{video_id}`...",
                parse_mode="Markdown"
            )
            from src.orchestrator import process_inspiration_approval
            import threading
            thread = threading.Thread(target=process_inspiration_approval, args=(video_id,))
            thread.start()
        else:
            await update.message.reply_text(
                f"🗑️ *Inspiration Script Rejected via Explicit Tag.*\nDiscarded copy for video ID `{video_id}`.",
                parse_mode="Markdown"
            )
        return

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
    
    # Add handler for button callbacks (Approve/Reject) (legacy fallback)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add handler for tagging approvals and pasted YouTube inspiration URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_approval))
    
    # Add handlers for runtime config updates
    application.add_handler(CommandHandler("update_inworld_key", update_inworld_key))
    application.add_handler(CommandHandler("update_inworld_secret", update_inworld_secret))
    application.add_handler(CommandHandler("update_voice_id", update_voice_id))
    application.add_handler(CommandHandler("update_deepgram_key", update_deepgram_key))
    application.add_handler(CommandHandler("find_visuals", find_visuals))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("process_url", process_url))
    
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
