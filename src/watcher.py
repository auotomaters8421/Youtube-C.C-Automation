import json
import os
import datetime
import logging
from pymongo import MongoClient
from src.config import Config
from src.monitor import fetch_feed

class SeenManager:
    """Handles persistence of seen video IDs."""
    
    def __init__(self, mongo_uri=None, json_path=None):
        self.mongo_uri = mongo_uri
        self.json_path = json_path or Config.SEEN_VIDEOS_PATH
        self.use_mongo = bool(self.mongo_uri)
        self.seen_cache = None
        
        if self.use_mongo:
            try:
                self.client = MongoClient(self.mongo_uri)
                self.db = self.client.youtube_automation
                self.collection = self.db.seen_videos
                logging.info("Using MongoDB for video persistence.")
            except Exception as e:
                logging.error(f"Failed to connect to MongoDB: {e}. Falling back to JSON.")
                self.use_mongo = False

    def is_seen(self, video_id):
        if self.use_mongo:
            return self.collection.find_one({"video_id": video_id}) is not None
        else:
            if self.seen_cache is None:
                self._load_json()
            return video_id in self.seen_cache

    def add_seen(self, video_id, title=None):
        if self.use_mongo:
            self.collection.insert_one({
                "video_id": video_id,
                "title": title,
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
        else:
            if self.seen_cache is None:
                self._load_json()
            if video_id not in self.seen_cache:
                self.seen_cache.append(video_id)
                self._save_json()

    def _load_json(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                try:
                    self.seen_cache = json.load(f)
                except json.JSONDecodeError:
                    self.seen_cache = []
        else:
            self.seen_cache = []

    def _save_json(self):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, "w") as f:
            json.dump(self.seen_cache, f, indent=4)

def check_for_new_videos(seen_file_path=None, min_date=None):
    """
    Checks for new Shorts in the configured channels.
    """
    manager = SeenManager(mongo_uri=Config.MONGO_URI, json_path=seen_file_path)
        
    if min_date is None:
        # Default to May 10, 2026
        min_date = datetime.datetime(2026, 5, 10, tzinfo=datetime.timezone.utc)

    new_videos_list = []
    
    for channel_id in Config.CHANNELS:
        entries = fetch_feed(channel_id)
        for entry in entries:
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                else:
                    pub_date = datetime.datetime.now(datetime.timezone.utc)
            except:
                pub_date = datetime.datetime.now(datetime.timezone.utc)
            
            if pub_date >= min_date and not manager.is_seen(entry.id):
                new_videos_list.append({
                    "title": entry.title,
                    "id": entry.id,
                    "link": entry.link,
                    "published": pub_date.isoformat()
                })
                manager.add_seen(entry.id, title=entry.title)

    return new_videos_list
