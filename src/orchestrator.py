import os
import datetime
import time
import json
from src.config import Config
from src.monitor import fetch_feed, fetch_video_metrics, fetch_transcript
from src.selector import select_topic, rank_shorts, reframe_transcript, reframe_as_inspiration
from src.audio import generate_tts
from src.telegram_bot import send_approval_request
from src.watcher import check_for_new_videos

def process_short_approval(video_id, title, include_sources=False):
    """
    Handles the approval-based production flow for a specific video ID.
    """
    print(f"Starting production for video: {video_id} (include_sources={include_sources})")
    
    # 1. Fetch transcript
    transcript = fetch_transcript(video_id)
    if not transcript:
        from src.telegram_bot import send_message
        send_message(f"❌ No transcript found for video: {title} ({video_id}). Production halted.")
        print(f"No transcript found for {video_id}")
        return

    # 2. Reframe via Gemini (Strategy A: Dual-Mode)
    print("Reframing transcript via Gemini (Dual-Mode)...")
    reframed_data = reframe_transcript(transcript)
    
    if "error" in reframed_data:
        from src.telegram_bot import send_message
        send_message(f"❌ Gemini Reframing Error: {reframed_data['error']}")
        return

    # 3. Create directory structure
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
    output_path = os.path.join(Config.OUTPUT_DIR, f"{date_str}_{safe_title}_{video_id}")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Save the reframed scripts as JSON for reference
    with open(os.path.join(output_path, "scripts.json"), "w", encoding="utf-8") as f:
        json.dump(reframed_data, f, indent=2)

    # 4. Generate audio ONLY for viral version
    v_data = reframed_data.get("viral_version")
    if v_data:
        outro = "AI is moving fast – your need to move even fast"
        full_text = f"{v_data['hook']} {v_data['body']} {v_data['cta']} {outro}"
        audio_file = os.path.join(output_path, "audio_viral_version.mp3")
        print(f"Generating TTS for viral_version via Inworld...")
        
        while True:
            try:
                from src.audio import generate_tts, InworldCreditError
                generate_tts(full_text, audio_file)
                break # Success!
            except InworldCreditError as e:
                from src.telegram_bot import send_message
                alert_text = (
                    f"⚠️ *Inworld Credits Exhausted!*\n\n"
                    f"Production for *{title}* is paused.\n"
                    f"Please update your API credentials using:\n"
                    f"`/update_inworld_key <key>`\n"
                    f"`/update_inworld_secret <secret>`\n"
                    f"`/update_voice_id <id>`\n\n"
                    f"The system will automatically resume once keys are updated."
                )
                send_message(alert_text)
                print(f"Paused: Waiting for Inworld credentials update... {e}")
                
                # Capture current keys to detect change
                old_key = Config.INWORLD_KEY
                old_secret = Config.INWORLD_SECRET
                old_voice = Config.INWORLD_VOICE_ID
                
                # Wait for any of them to change
                while Config.INWORLD_KEY == old_key and \
                      Config.INWORLD_SECRET == old_secret and \
                      Config.INWORLD_VOICE_ID == old_voice:
                    time.sleep(10) # Check every 10 seconds
                
                print("New credentials detected! Resuming production...")
                send_message(f"🚀 New credentials detected. Resuming production for: {title}")
                
            except Exception as e:
                print(f"TTS Error for viral_version: {e}")
                break # Fatal error, stop trying

    # 5. Optionally fetch visual sources using DuckDuckGo search and Gemini
    sources_text = ""
    if include_sources:
        try:
            print("Fetching visual sources for successful production notification...")
            # Extract script text to derive query
            script_text = ""
            if v_data:
                script_text = f"{v_data.get('hook', '')} {v_data.get('body', '')}"
            if not script_text:
                script_text = reframed_data.get("standard_version", {}).get("body", "")
            if not script_text:
                script_text = str(reframed_data)

            import google.generativeai as genai
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Analyze the following script and extract the most relevant search query (just 2-5 words) to find the official blog post, official website, or visual sources for the AI tool or topic mentioned. Return ONLY the search query string, nothing else. Script: {script_text}"
            response = model.generate_content(prompt)
            query = response.text.strip()
            
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=3):
                    results.append(f"[{r['title']}]({r['href']})")
            if results:
                sources_text = f"\n\n🔗 *Visual Sources found for query '{query}':*\n" + "\n".join(results)
            else:
                sources_text = f"\n\n🔗 No visual sources found for query: `{query}`"
        except Exception as e:
            print(f"Error fetching visual sources: {e}")
            sources_text = f"\n\n⚠️ Failed to fetch visual sources: {e}"

    # 6. Notify and send files
    from src.telegram_bot import send_message, send_file, send_audio
    send_message(f"✅ Production completed for: {title}\nViral MP3 and Scripts generated.{sources_text}")
    
    scripts_file = os.path.join(output_path, "scripts.json")
    send_file(scripts_file, caption=f"Scripts for {title}")
    
    audio_file = os.path.join(output_path, "audio_viral_version.mp3")
    if os.path.exists(audio_file):
        send_audio(audio_file, caption=f"Viral Version - {title}", title=f"Viral - {video_id}")
    else:
        send_message(f"❌ Error: Viral MP3 was not generated for {title}")

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
        include_sources = video_data.get('include_sources', False)
        process_short_approval(video_id, title, include_sources=include_sources)
        return

    from src.watcher import SeenManager
    manager = SeenManager(mongo_uri=Config.MONGO_URI)

    all_shorts = []
    for channel_id in Config.CHANNELS:
        print(f"Fetching shorts for channel: {channel_id}")
        shorts = fetch_feed(channel_id)
        for short in shorts:
            video_id = short.get('yt_videoid')
            if not video_id:
                continue
            if manager.is_seen(video_id):
                print(f"Skipping already recommended/seen video: {video_id}")
                continue
            
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
    
    # Send top 5 for approval
    top_n = ranked[:5]
    print(f"Identifying top {len(top_n)} videos for approval.")
    
    for i, video in enumerate(top_n):
        print(f"Sending recommendation {i+1}: {video['title']} (Velocity: {video.get('velocity', 0):.2f})")
        send_approval_request(video)
        manager.add_seen(video['yt_videoid'], title=video['title'])
        
    print(f"Sent {len(top_n)} approval requests to Telegram. Waiting for user to click GO on any of them...")

def process_inspiration_url(video_id, title):
    """
    Handles the first step of the inspiration workflow:
    Fetches transcript, rewrites it via Gemini 1.5 Pro, and sends the copy
    to the user for review with an approval hashtag. Does NOT generate TTS yet.
    """
    print(f"Starting step 1 of inspiration production for video: {video_id} - {title}")
    
    # 1. Fetch transcript
    transcript = fetch_transcript(video_id)
    if not transcript:
        from src.telegram_bot import send_message
        send_message(f"❌ No transcript found for inspiration video: {title} ({video_id}). Cloning halted.")
        print(f"No transcript found for {video_id}")
        return

    # 2. Reframe via Gemini (Inspiration/Clone mode using gemini-1.5-pro)
    print("Reframing transcript via Gemini Pro (Inspiration Mode)...")
    reframed_data = reframe_as_inspiration(transcript)
    
    if "error" in reframed_data:
        from src.telegram_bot import send_message
        send_message(f"❌ Gemini Inspiration Cloning Error: {reframed_data['error']}")
        return

    # 3. Create directory structure
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
    output_path = os.path.join(Config.OUTPUT_DIR, f"{date_str}_inspiration_{safe_title}_{video_id}")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Save the reframed scripts as JSON for reference
    with open(os.path.join(output_path, "scripts.json"), "w", encoding="utf-8") as f:
        json.dump(reframed_data, f, indent=2)

    # 4. Notify user and present script copy for approval before voice generation
    from src.telegram_bot import send_message, send_file
    
    techniques = reframed_data.get("psychological_techniques_used", "Pro clone")
    v_data = reframed_data.get("viral_version", {})
    s_data = reframed_data.get("standard_version", {})
    
    tag = f"#insp_approve_{video_id}"
    
    msg = (
        f"🎯 *Inspiration Copy Generated (Gemini Pro)*\n\n"
        f"*Original:* {title}\n"
        f"*Psychological Angles:* {techniques}\n\n"
        f"🔥 *Viral Copy:*\n"
        f"• *Hook:* {v_data.get('hook')}\n"
        f"• *Body:* {v_data.get('body')}\n"
        f"• *CTA:* {v_data.get('cta')}\n\n"
        f"ℹ️ *Standard Copy:*\n"
        f"• *Hook:* {s_data.get('hook')}\n"
        f"• *Body:* {s_data.get('body')}\n"
        f"• *CTA:* {s_data.get('cta')}\n\n"
        f"🏷️ *Tag:* `{tag}`\n\n"
        f"To generate the TTS voice/audio for this copy:\n"
        f"1. *Reply* to this message with `approve` or `reject`\n"
        f"2. Or *type* `{tag} approve` anywhere in the chat."
    )
    
    send_message(msg)
    
    scripts_file = os.path.join(output_path, "scripts.json")
    send_file(scripts_file, caption=f"Scripts JSON for {title}")
    print(f"Step 1 completed. Script sent for approval to Telegram for: {video_id}")

def process_inspiration_approval(video_id):
    """
    Handles step 2 of the inspiration workflow:
    Generates TTS voice audio for an approved inspiration copy and delivers it.
    """
    print(f"Starting step 2 (audio production) for inspiration copy: {video_id}")
    
    # 1. Locate folder matching the video ID in output directory
    output_dir = Config.OUTPUT_DIR
    target_folder = None
    if os.path.exists(output_dir):
        for folder in os.listdir(output_dir):
            if folder.startswith("20") and "inspiration" in folder and folder.endswith(f"_{video_id}"):
                target_folder = os.path.join(output_dir, folder)
                break

    if not target_folder:
        from src.telegram_bot import send_message
        send_message(f"❌ Error: Could not locate the rewritten copy folder for video ID `{video_id}`.")
        print(f"Inspiration folder not found for {video_id}")
        return

    scripts_file = os.path.join(target_folder, "scripts.json")
    if not os.path.exists(scripts_file):
        from src.telegram_bot import send_message
        send_message(f"❌ Error: scripts.json is missing from target folder `{target_folder}`.")
        return

    # 2. Load the scripts
    try:
        with open(scripts_file, "r", encoding="utf-8") as f:
            reframed_data = json.load(f)
    except Exception as e:
        from src.telegram_bot import send_message
        send_message(f"❌ Error loading script JSON: {e}")
        return

    # Extract original title from the folder name
    # Folder structure: YYYY-MM-DD_inspiration_title_videoid
    folder_name = os.path.basename(target_folder)
    parts = folder_name.split("_inspiration_")
    title = video_id
    if len(parts) > 1:
        # Strip trailing _videoid
        title_with_id = parts[1]
        title = title_with_id.rsplit(f"_{video_id}", 1)[0].replace("_", " ")

    # 3. Generate Audio for Viral Version
    v_data = reframed_data.get("viral_version")
    if not v_data:
        from src.telegram_bot import send_message
        send_message("❌ Error: 'viral_version' script is missing from stored JSON.")
        return

    outro = "AI is moving fast – your need to move even fast"
    full_text = f"{v_data['hook']} {v_data['body']} {v_data['cta']} {outro}"
    audio_file = os.path.join(target_folder, "audio_viral_version.mp3")
    
    print(f"Generating TTS for viral_version via Inworld...")
    from src.telegram_bot import send_message
    send_message(f"⏳ Generating TTS voice audio for *{title}*... Please wait.")
    
    while True:
        try:
            from src.audio import generate_tts, InworldCreditError
            generate_tts(full_text, audio_file)
            break # Success!
        except InworldCreditError as e:
            alert_text = (
                f"⚠️ *Inworld Credits Exhausted!*\n\n"
                f"Production for inspiration copy *{title}* is paused.\n"
                f"Please update your API credentials using:\n"
                f"`/update_inworld_key <key>`\n"
                f"`/update_inworld_secret <secret>`\n"
                f"`/update_voice_id <id>`\n\n"
                f"The system will automatically resume once keys are updated."
            )
            send_message(alert_text)
            print(f"Paused: Waiting for Inworld credentials update... {e}")
            
            # Capture current keys to detect change
            old_key = Config.INWORLD_KEY
            old_secret = Config.INWORLD_SECRET
            old_voice = Config.INWORLD_VOICE_ID
            
            # Wait for any of them to change
            while Config.INWORLD_KEY == old_key and \
                  Config.INWORLD_SECRET == old_secret and \
                  Config.INWORLD_VOICE_ID == old_voice:
                time.sleep(10) # Check every 10 seconds
            
            print("New credentials detected! Resuming production...")
            send_message(f"🚀 New credentials detected. Resuming production for: {title}")
            
        except Exception as e:
            print(f"TTS Error for viral_version: {e}")
            send_message(f"❌ Audio Generation Error: {e}")
            return

    # 4. Deliver final audio to user
    from src.telegram_bot import send_audio
    if os.path.exists(audio_file):
        send_audio(audio_file, caption=f"Viral Copy - {title}", title=f"Inspiration - {video_id}")
        send_message(f"✅ *Audio Production Completed!* Delivered viral voice MP3 for: *{title}*")
    else:
        send_message(f"❌ Error: MP3 was not found after generation.")

if __name__ == "__main__":
    run_automation()
