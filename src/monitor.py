import feedparser
import requests
import re
from youtube_transcript_api import YouTubeTranscriptApi

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
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(url, timeout=10)
        # Regex to find views in meta tag
        views_match = re.search(r'<meta itemprop="interactionCount" content="(\d+)">', response.text)
        views = int(views_match.group(1)) if views_match else 0
        
        # Regex to find upload date
        date_match = re.search(r'<meta itemprop="datePublished" content="([^"]+)">', response.text)
        publish_date = date_match.group(1) if date_match else None
        
        return {
            'views': views,
            'publish_date': publish_date
        }
    except:
        return {'views': 0, 'publish_date': None}

def fetch_transcript(video_id):
    """
    Fetches the transcript for a given video ID.
    Returns the combined text string or None if it fails.
    """
    try:
        # Instantiate the API and use 'fetch' for version 1.2.4+
        transcript_list = YouTubeTranscriptApi().fetch(video_id)
        return " ".join([segment['text'] for segment in transcript_list])
    except:
        return None
