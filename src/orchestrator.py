import os
import datetime
import time
from src.config import Config
from src.monitor import fetch_feed, fetch_video_metrics, fetch_transcript
from src.selector import select_topic, rank_shorts, reframe_transcript
from src.audio import generate_tts
from src.telegram_bot import send_approval_request
from src.watcher import check_for_new_videos

def process_short_approval(video_id, title):
    """
    Handles the approval-based production flow for a specific video ID.
    """
    print(f"Starting production for video: {video_id}")
    
    # 1. Fetch transcript
    transcript = fetch_transcript(video_id)
    if not transcript:
        from src.telegram_bot import send_message
        send_message(f"❌ No transcript found for video: {title} ({video_id}). Production halted.")
        print(f"No transcript found for {video_id}")
        return

    # 2. Reframe via Gemini
    print("Reframing transcript via Gemini...")
    reframed_script = reframe_transcript(transcript)

    # 3. Create directory structure
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
    output_path = os.path.join(Config.OUTPUT_DIR, f"{date_str}_{safe_title}")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 4. Generate audio via Inworld
    audio_file = os.path.join(output_path, "audio.mp3")
    print("Generating TTS via Inworld...")
    generate_tts(reframed_script, audio_file)

    # 5. Notify user via Telegram
    from src.telegram_bot import send_message
    send_message(f"✅ Production completed for: {title}\nFiles saved in: {output_path}")
    print(f"Production completed for {video_id}")

def run_automation(video_data=None):
    """
    Main orchestration logic to fetch feeds, rank shorts, and send top recommendation to Telegram.
    If video_data is provided, it processes that specific video immediately (approval-less).
    """
    if not os.path.exists(Config.OUTPUT_DIR):
        os.makedirs(Config.OUTPUT_DIR)

    if video_data:
        video_id = video_data.get('yt_videoid') or video_data.get('id')
        title = video_data.get('title', 'Unknown')
        process_short_approval(video_id, title)
        return

    all_shorts = []
    for channel_id in Config.CHANNELS:
        print(f"Fetching shorts for channel: {channel_id}")
        shorts = fetch_feed(channel_id)
        for short in shorts:
            video_id = short.get('yt_videoid')
            metrics = fetch_video_metrics(video_id)
            short['views'] = metrics['views']
            # Convert publish_date to timestamp
            # publish_date is usually "2024-05-13T10:00:00+00:00"
            try:
                dt = datetime.datetime.fromisoformat(metrics['publish_date'].replace('Z', '+00:00'))
                short['upload_time'] = dt.timestamp()
            except:
                short['upload_time'] = time.time()
            all_shorts.append(short)

    if not all_shorts:
        print("No new shorts found.")
        return

    # Rank shorts
    ranked = rank_shorts(all_shorts)
    top_video = ranked[0]
    
    print(f"Top video identified: {top_video['title']} with view velocity {top_video.get('velocity', 0):.2f}")
    
    # Send for approval
    send_approval_request(top_video)
    print("Approval request sent to Telegram. Waiting for user to click GO...")

if __name__ == "__main__":
    run_automation()
