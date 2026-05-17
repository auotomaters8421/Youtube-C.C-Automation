import pytest
from unittest.mock import patch, MagicMock

def test_fetch_feed():
    from src.monitor import fetch_feed
    
    # Mocking feedparser.parse and is_short
    with patch('feedparser.parse') as mock_parse, \
         patch('src.monitor.is_short') as mock_is_short:
        
        mock_feed = MagicMock()
        mock_feed.entries = [
            {'title': 'Short Video', 'yt_videoid': 'short1'},
            {'title': 'Long Video', 'yt_videoid': 'long1'}
        ]
        mock_parse.return_value = mock_feed
        
        # Mock is_short to return True only for 'short1'
        mock_is_short.side_effect = lambda x: x == 'short1'
        
        entries = fetch_feed("UC12345")
        
        # Verify feedparser.parse was called with the correct URL
        expected_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC12345"
        mock_parse.assert_called_once_with(expected_url)
        
        # Verify only the short is returned
        assert len(entries) == 1
        assert entries[0]['title'] == 'Short Video'

def test_fetch_transcript_invalid():
    from src.monitor import fetch_transcript
    with patch('src.monitor.YouTubeTranscriptApi.fetch') as mock_fetch:
        mock_fetch.side_effect = Exception("Failed")
        assert fetch_transcript("invalid_id") is None

def test_fetch_transcript_success():
    from src.monitor import fetch_transcript
    with patch('src.monitor.YouTubeTranscriptApi.fetch') as mock_fetch:
        mock_fetch.return_value = [
            {'text': 'Hello'},
            {'text': 'World'}
        ]
        
        result = fetch_transcript("valid_id")
        assert result == "Hello World"

def test_fetch_video_metrics():
    from src.monitor import fetch_video_metrics
    # Mocking requests.get to return a page with some view counts
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        # Simple HTML content containing views and publish date
        mock_response.text = '<html><body><meta itemprop="interactionCount" content="12345"><meta itemprop="datePublished" content="2023-10-27"></body></html>'
        mock_get.return_value = mock_response
        
        metrics = fetch_video_metrics("some_id")
        assert metrics['views'] == 12345
        assert metrics['publish_date'] == "2023-10-27"
