import feedparser
import requests
import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
from src.config import Config


def fetch_transcript_supadata(video_id: str) -> str | None:
    """
    Phase 1.5: Fetches transcript via Supadata API (free, no auth).
    Bypasses YouTube bot detection by fetching from their servers.
    Docs: https://supadata.ai/documentation/youtube/get-transcript
    """
    import logging
    try:
        url = f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}&text=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # Response shape: {"content": "...", "lang": "en", ...}
            content = data.get("content", "") or ""
            if content.strip():
                logging.info(f"Phase 1.5 (Supadata): Got transcript for {video_id} ({len(content)} chars)")
                return content.strip()
        logging.warning(f"Phase 1.5 (Supadata): No transcript for {video_id} (status={resp.status_code})")
    except Exception as e:
        logging.warning(f"Phase 1.5 (Supadata) failed for {video_id}: {e}")
    return None

def is_short(video_id):
    """
    Checks if a video is a YouTube Short by probing the shorts URL.
    Returns True if it's a Short, False otherwise.
    """
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        # We allow redirects to see where it lands.
        # If it's a short, it stays on /shorts/ or redirects to the same.
        # If it's a long video, it redirects to /watch?v=
        response = requests.head(url, allow_redirects=True, timeout=5)
        return "/shorts/" in response.url
    except:
        return False

def fetch_feed(channel_id):
    """
    Fetches the RSS feed for a given YouTube channel ID and filters for Shorts.
    """
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    
    shorts = []
    for entry in feed.entries:
        video_id = entry.get("yt_videoid")
        if video_id and is_short(video_id):
            shorts.append(entry)
            
    return shorts

def fetch_video_metrics(video_id):
    """
    Fetches views for a given video ID using simple scraping.
    """
    urls = [
        f"https://www.youtube.com/shorts/{video_id}",
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # Strategy 1: itemprop meta tag
            views_match = re.search(r'<meta itemprop="interactionCount" content="(\d+)">', response.text)
            views = int(views_match.group(1)) if views_match else 0
            
            # Strategy 2: "viewCount":"..." in JSON blob
            if views == 0:
                json_match = re.search(r'\"viewCount\":\{\"simpleText\":\"([\d,]+)\"', response.text)
                if json_match:
                    views = int(json_match.group(1).replace(',', ''))
                else:
                    json_match = re.search(r'\"viewCount\":\"(\d+)\"', response.text)
                    views = int(json_match.group(1)) if json_match else 0
            
            # Strategy 3: "label":"... views"
            if views == 0:
                label_match = re.search(r'\"label\":\"([\d,.]+)[^"]*views\"', response.text)
                if label_match:
                    val = label_match.group(1).replace(',', '')
                    if 'K' in val: views = int(float(val.replace('K', '')) * 1000)
                    elif 'M' in val: views = int(float(val.replace('M', '')) * 1000000)
                    else: views = int(float(val))
            
            if views > 0:
                # Regex to find upload date
                date_match = re.search(r'<meta itemprop="datePublished" content="([^"]+)">', response.text)
                publish_date = date_match.group(1) if date_match else None
                
                return {
                    'views': views,
                    'publish_date': publish_date
                }
        except:
            continue
            
    return {'views': 0, 'publish_date': None}

def fetch_transcript(video_id):
    """
    Fetches the transcript for a given video ID.
    Uses Phase 1 (Free YouTube Transcript API) first, falls back to
    Phase 2 (Deepgram transcription) if Phase 1 fails.
    """
    import logging
    # Try Phase 1: Free API
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        text_snippets = []
        for snippet in transcript_list:
            if hasattr(snippet, 'text'):
                text_snippets.append(snippet.text)
            elif isinstance(snippet, dict) and 'text' in snippet:
                text_snippets.append(snippet['text'])
            else:
                try:
                    text_snippets.append(snippet['text'])
                except:
                    text_snippets.append(str(snippet))
        result = " ".join(text_snippets).strip()
        if result:
            return result
        logging.warning(f"Phase 1 returned empty transcript for {video_id}. Trying Phase 2...")
    except Exception as e:
        logging.info(f"Phase 1 transcript fetch failed for {video_id}: {e}. Trying Phase 2 (Deepgram)...")

    # --- Phase 1.5: Supadata API (free, no bot-check) ---
    transcript = fetch_transcript_supadata(video_id)
    if transcript:
        return transcript
    logging.warning(f"Phase 1.5 (Supadata) gave nothing for {video_id}. Trying Phase 2 (Deepgram)...")

    # Try Phase 2: Deepgram Fallback
    import tempfile
    temp_dir = tempfile.gettempdir()
    audio_base = os.path.join(temp_dir, f"temp_audio_{video_id}")
    # Use cross-platform temporary directory which works on Windows and Render
    audio_path = None
    try:
        audio_path = download_audio(video_id, audio_base)
        if not audio_path:
            logging.error(f"Phase 2: Audio download returned no file for {video_id}")
            return None
        transcript = transcribe_audio_deepgram(audio_path)
        # Validate transcript is non-empty and not just whitespace
        if transcript and transcript.strip():
            return transcript.strip()
        logging.error(f"Phase 2: Deepgram returned empty/null transcript for {video_id}")
        return None
    except Exception as fallback_err:
        logging.error(f"Phase 2 transcript fetch failed for {video_id}: {fallback_err}")
        return None
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError as cleanup_err:
                logging.debug(f"Failed to cleanup temp audio {audio_path}: {cleanup_err}")

def download_audio(video_id, output_path):
    import yt_dlp
    import logging
    import os
    import glob
    
    # Remove existing matching files if any
    for f in glob.glob(output_path + '*'):
        try:
            os.remove(f)
        except Exception as e:
            logging.debug(f"Failed to remove old temp file {f}: {e}")

    import shutil
    ffmpeg_available = shutil.which("ffmpeg") is not None

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': output_path + '.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        # Rotate through clients most likely to bypass bot check in cloud env
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'android_vr', 'android', 'ios', 'web']
            }
        },
        # Throttle/sleep to avoid immediate bot detection
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        # Browser-like HTTP headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    }
    
    if Config.YOUTUBE_COOKIES_PATH and os.path.exists(Config.YOUTUBE_COOKIES_PATH):
        ydl_opts['cookiefile'] = Config.YOUTUBE_COOKIES_PATH
        logging.info(f"Using YouTube cookies from: {Config.YOUTUBE_COOKIES_PATH}")
    elif Config.YOUTUBE_COOKIES_BASE64:
        import base64
        import tempfile
        try:
            # Decode base64 cookies to a temporary file
            cookie_data = base64.b64decode(Config.YOUTUBE_COOKIES_BASE64)
            temp_cookie_file = os.path.join(tempfile.gettempdir(), f"youtube_cookies_{video_id}.txt")
            with open(temp_cookie_file, "wb") as f:
                f.write(cookie_data)
            ydl_opts['cookiefile'] = temp_cookie_file
            logging.info(f"Using YouTube cookies from decoded Base64 string.")
            # Note: We don't delete it immediately as yt-dlp needs it during download
        except Exception as e:
            logging.error(f"Failed to decode YOUTUBE_COOKIES_BASE64: {e}")
    
    if ffmpeg_available:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        logging.info("ffmpeg not found on PATH. Downloading audio in raw format without conversion.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
        # Find the downloaded file using glob
        downloaded_files = glob.glob(output_path + '*')
        if downloaded_files:
            audio_file = downloaded_files[0]
            # Validate file is non-empty
            file_size = os.path.getsize(audio_file)
            if file_size == 0:
                logging.error(f"Downloaded audio file is 0 bytes for {video_id}: {audio_file}")
                os.remove(audio_file)
                return None
            logging.info(f"Audio downloaded for {video_id}: {audio_file} ({file_size} bytes)")
            return audio_file
            
        logging.error(f"Download succeeded but no file found starting with {output_path}")
        return None
    except Exception as e:
        logging.error(f"Failed to download audio for {video_id}: {e}")
        return None


def transcribe_audio_deepgram(audio_path):
    import logging
    
    if not Config.DEEPGRAM_KEY:
        logging.error("Deepgram API key is not configured. Skipping transcription.")
        return None
    
    # Validate file exists and is non-empty before sending to Deepgram
    if not os.path.exists(audio_path):
        logging.error(f"Audio file does not exist: {audio_path}")
        return None
    
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        logging.error(f"Audio file is empty (0 bytes): {audio_path}")
        return None
    
    import sys
    from unittest.mock import MagicMock
    if 'pyaudio' not in sys.modules:
        sys.modules['pyaudio'] = MagicMock()
        
    from deepgram import (
        DeepgramClient,
        PrerecordedOptions,
        FileSource,
    )
    try:
        deepgram = DeepgramClient(Config.DEEPGRAM_KEY)
        with open(audio_path, "rb") as file:
            buffer_data = file.read()
        
        # Detect mimetype from file extension
        ext = os.path.splitext(audio_path)[1].lower()
        mime_map = {
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.webm': 'audio/webm',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
        }
        mimetype = mime_map.get(ext, 'audio/mpeg')
        
        payload: FileSource = {"buffer": buffer_data, "mimetype": mimetype}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="en",
        )
        
        logging.info(f"Sending {file_size} bytes ({mimetype}) to Deepgram for transcription...")
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        
        # Safely check response structure
        if not response or not hasattr(response, 'results'):
            logging.error("Deepgram returned no results object")
            return None
            
        results = response.results
        if not hasattr(results, 'channels') or not results.channels:
            logging.error("Deepgram returned no channels in results")
            return None
            
        channel = results.channels[0]
        if not hasattr(channel, 'alternatives') or not channel.alternatives:
            logging.error("Deepgram returned no alternatives in channel")
            return None
        
        transcript = channel.alternatives[0].transcript
        
        # Validate transcript is meaningful
        if not transcript or not transcript.strip():
            logging.warning(f"Deepgram returned empty transcript for {audio_path}")
            return None
        
        logging.info(f"Deepgram transcription successful: {len(transcript)} chars")
        return transcript.strip()
    except Exception as e:
        logging.error(f"Deepgram Error: {e}")
        return None
