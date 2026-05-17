import json
import os
import datetime
from src.config import Config
from src.monitor import fetch_feed

def check_for_new_videos(seen_file_path=None, min_date=None):
    """
    Checks for new Shorts in the configured channels.
    'New' is defined as:
    1. Uploaded on or after min_date (defaults to 2026-05-10).
    2. Not present in the seen_videos.json file.
    """
    if seen_file_path is None:
        seen_file_path = Config.SEEN_VIDEOS_PATH
        
    if min_date is None:
        # Default to May 10, 2026
        min_date = datetime.datetime(2026, 5, 10, tzinfo=datetime.timezone.utc)

    # Ensure the directory for the seen file exists
    os.makedirs(os.path.dirname(seen_file_path), exist_ok=True)

    if os.path.exists(seen_file_path):
        with open(seen_file_path, "r") as f:
            try:
                seen_videos = json.load(f)
            except json.JSONDecodeError:
                seen_videos = []
    else:
        seen_videos = []

    new_videos_list = []
    
    for channel_id in Config.CHANNELS:
        entries = fetch_feed(channel_id)
        for entry in entries:
            # entry.published is usually a time tuple or a datetime object depending on feedparser
            # We convert it to a timezone-aware datetime for comparison
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                else:
                    # Fallback to current time if date is missing
                    pub_date = datetime.datetime.now(datetime.timezone.utc)
            except:
                pub_date = datetime.datetime.now(datetime.timezone.utc)
            
            if pub_date >= min_date and entry.id not in seen_videos:
                new_videos_list.append({
                    "title": entry.title,
                    "id": entry.id,
                    "link": entry.link,
                    "published": pub_date.isoformat()
                })
                seen_videos.append(entry.id)

    with open(seen_file_path, "w") as f:
        json.dump(seen_videos, f, indent=4)

    return new_videos_list
