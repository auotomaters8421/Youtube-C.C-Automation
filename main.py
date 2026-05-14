import logging
import time
import datetime
import schedule
from src.orchestrator import run_automation
from src.telegram_bot import start_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)

def run_scheduled_automation():
    logging.info("Running scheduled Short discovery...")
    try:
        run_automation()
    except Exception as e:
        logging.error(f"Error in scheduled automation: {e}")

def main():
    """
    Main entry point for the YouTube Shorts Reframer.
    Starts the discovery and bot flow.
    """
    logging.info("YouTube Automation Bot Starting...")
    
    # 1. Schedule discovery every 6 hours
    schedule.every(6).hours.do(run_scheduled_automation)
    
    # 2. Run initial discovery immediately
    run_scheduled_automation()
    
    try:
        # 3. Start the Telegram bot to handle approvals and callbacks
        # We start it in non-blocking mode to allow the scheduler to run in the main thread
        logging.info("Starting Telegram bot handler (non-blocking)...")
        application = start_bot(run=False)
        
        # Keep the main thread alive for the scheduler
        logging.info("Main loop running. Discovery scheduled every 6 hours.")
        while True:
            schedule.run_pending()
            time.sleep(1) # More responsive than 60s
            
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Critical error in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    main()
