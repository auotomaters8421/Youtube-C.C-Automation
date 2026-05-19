import feedparser
import requests
import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
from src.config import Config

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
    Returns the combined text string or None if it fails.
    """
    try:
        # In version 1.2.4, we need to instantiate the API
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        # Extract text from the list of snippets
        return " ".join([snippet['text'] for snippet in transcript_list])
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch transcript for {video_id}: {e}")
        return None

def download_audio(video_id, output_path):
    import yt_dlp
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return f"{output_path}.m4a"

def transcribe_audio_deepgram(audio_path):
    if not Config.DEEPGRAM_KEY:
        return None
    
    from deepgram import (
        DeepgramClient,
        PrerecordedOptions,
        FileSource,
    )
    try:
        deepgram = DeepgramClient(Config.DEEPGRAM_KEY)
        with open(audio_path, "rb") as file:
            buffer_data = file.read()
        
        payload: FileSource = {"buffer": buffer_data}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )
        
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        return response.results.channels[0].alternatives[0].transcript
    except Exception as e:
        import logging
        logging.error(f"Deepgram Error: {e}")
        return None
