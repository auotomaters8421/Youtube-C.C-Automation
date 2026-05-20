import logging
import time
import datetime
import schedule
import threading
import uvicorn
import asyncio
from fastapi import FastAPI
from src.orchestrator import run_automation
from src.telegram_bot import start_bot
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# --- HEARTBEAT WEB SERVER ---
app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "YouTube Automation Bot is running",
        "timestamp": datetime.datetime.now().isoformat()
    }

def run_web_server():
    """Runs the FastAPI server on port 7860."""
    logging.info("Starting Heartbeat Web Server on port 7860...")
    uvicorn.run(app, host="0.0.0.0", port=7860)

# --- AUTOMATION LOGIC ---

def run_scheduled_automation():
    logging.info("Running scheduled Short discovery...")
    try:
        run_automation()
    except Exception as e:
        logging.error(f"Error in scheduled automation: {e}")

def scheduler_loop():
    """Background thread for the schedule manager."""
    logging.info("Scheduler loop started. Discovery scheduled every 6 hours.")
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """
    Main entry point for the YouTube Shorts Reframer.
    Starts the discovery, bot flow, and heartbeat server.
    """
    logging.info("YouTube Automation Bot Starting...")
    
    # 1. Validate Config
    Config.validate()
    
    # 2. Start the Heartbeat Web Server (Daemon Thread)
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # 3. Setup Scheduling
    schedule.every(6).hours.do(run_scheduled_automation)
    
    # 4. Start the Scheduler (Daemon Thread)
    sched_thread = threading.Thread(target=scheduler_loop, daemon=True)
    sched_thread.start()
    
    # 5. Run initial discovery immediately
    # We do this after threads start to ensure web server is up
    run_scheduled_automation()
    
    bot_retry_delay = 10
    while True:
        try:
            # 6. Start the Telegram bot (BLOCKING)
            # We run the bot in the main thread because it handles signals (Ctrl+C) better
            logging.info("Starting Telegram bot handler (Blocking)...")
            start_bot(run=True)
            break
        except KeyboardInterrupt:
            logging.info("Bot stopped by user.")
            break
        except Exception as e:
            logging.error(f"Critical error in bot loop: {e}. Retrying in {bot_retry_delay} seconds...")
            time.sleep(bot_retry_delay)


if __name__ == "__main__":
    main()
