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

def test_fetch_transcript_fallback_success():
    from src.monitor import fetch_transcript
    with patch('src.monitor.YouTubeTranscriptApi.fetch') as mock_fetch, \
         patch('src.monitor.download_audio') as mock_download, \
         patch('src.monitor.transcribe_audio_deepgram') as mock_transcribe, \
         patch('os.remove') as mock_remove, \
         patch('os.path.exists') as mock_exists:
        
        # Phase 1 fails
        mock_fetch.side_effect = Exception("Phase 1 Failed")
        
        # Phase 2 succeeds
        mock_download.return_value = "/tmp/temp_audio_fallback.m4a"
        mock_transcribe.return_value = "Fallback Transcript"
        mock_exists.return_value = True
        
        result = fetch_transcript("fallback_id")
        
        assert result == "Fallback Transcript"
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once_with("/tmp/temp_audio_fallback.m4a")
        mock_remove.assert_called_once_with("/tmp/temp_audio_fallback.m4a")

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

def test_download_audio_success():
    from src.monitor import download_audio
    with patch('yt_dlp.YoutubeDL') as mock_ydl, \
         patch('glob.glob') as mock_glob, \
         patch('os.path.getsize') as mock_getsize:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        mock_glob.return_value = ["output_path.mp3"]
        mock_getsize.return_value = 50000  # 50KB non-empty file
        
        result = download_audio("video123", "output_path")
        
        mock_instance.download.assert_called_once_with(["https://www.youtube.com/watch?v=video123"])
        assert result == "output_path.mp3"

def test_download_audio_zero_bytes():
    """Downloads that produce 0-byte files should return None."""
    from src.monitor import download_audio
    with patch('yt_dlp.YoutubeDL') as mock_ydl, \
         patch('glob.glob') as mock_glob, \
         patch('os.path.getsize') as mock_getsize, \
         patch('os.remove') as mock_remove:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        mock_glob.return_value = ["output_path.mp3"]
        mock_getsize.return_value = 0  # 0-byte file
        
        result = download_audio("video123", "output_path")
        
        assert result is None
        mock_remove.assert_called_with("output_path.mp3")

def test_download_audio_failure():
    from src.monitor import download_audio
    import yt_dlp
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        # Simulate DownloadError
        mock_instance.download.side_effect = Exception("Download failed")
        
        result = download_audio("video123", "output_path")
        assert result is None

def test_transcribe_audio_deepgram_success():
    from src.monitor import transcribe_audio_deepgram
    from src.config import Config
    Config.DEEPGRAM_KEY = "test_key"
    
    # Mock the entire deepgram module and its sub-attributes
    with patch.dict('sys.modules', {'deepgram': MagicMock()}):
        import deepgram
        mock_client = deepgram.DeepgramClient
        mock_deepgram = MagicMock()
        mock_client.return_value = mock_deepgram
        
        # Mocking the deepgram response structure
        mock_response = MagicMock()
        mock_response.results.channels = [
            MagicMock(alternatives=[MagicMock(transcript="Deepgram Transcript")])
        ]
        mock_deepgram.listen.prerecorded.v.return_value.transcribe_file.return_value = mock_response
        
        # Mock built-in open and os functions for file validation
        with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"audio data")))))), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            result = transcribe_audio_deepgram("dummy_path.mp3")
            assert result == "Deepgram Transcript"

def test_transcribe_audio_deepgram_empty_transcript():
    """Deepgram returning an empty string should be treated as failure."""
    from src.monitor import transcribe_audio_deepgram
    from src.config import Config
    Config.DEEPGRAM_KEY = "test_key"
    
    with patch.dict('sys.modules', {'deepgram': MagicMock()}):
        import deepgram
        mock_client = deepgram.DeepgramClient
        mock_deepgram = MagicMock()
        mock_client.return_value = mock_deepgram
        
        mock_response = MagicMock()
        mock_response.results.channels = [
            MagicMock(alternatives=[MagicMock(transcript="")])  # Empty string
        ]
        mock_deepgram.listen.prerecorded.v.return_value.transcribe_file.return_value = mock_response
        
        with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"audio data")))))), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            result = transcribe_audio_deepgram("dummy_path.mp3")
            assert result is None

def test_transcribe_audio_deepgram_whitespace_transcript():
    """Deepgram returning whitespace-only string should be treated as failure."""
    from src.monitor import transcribe_audio_deepgram
    from src.config import Config
    Config.DEEPGRAM_KEY = "test_key"
    
    with patch.dict('sys.modules', {'deepgram': MagicMock()}):
        import deepgram
        mock_client = deepgram.DeepgramClient
        mock_deepgram = MagicMock()
        mock_client.return_value = mock_deepgram
        
        mock_response = MagicMock()
        mock_response.results.channels = [
            MagicMock(alternatives=[MagicMock(transcript="   ")])  # Whitespace only
        ]
        mock_deepgram.listen.prerecorded.v.return_value.transcribe_file.return_value = mock_response
        
        with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"audio data")))))), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            result = transcribe_audio_deepgram("dummy_path.mp3")
            assert result is None

def test_transcribe_audio_deepgram_invalid_response():
    from src.monitor import transcribe_audio_deepgram
    from src.config import Config
    Config.DEEPGRAM_KEY = "test_key"
    
    # Mock the entire deepgram module and its sub-attributes
    with patch.dict('sys.modules', {'deepgram': MagicMock()}):
        import deepgram
        mock_client = deepgram.DeepgramClient
        mock_deepgram = MagicMock()
        mock_client.return_value = mock_deepgram
        
        # Mocking an empty response structure
        mock_response = MagicMock()
        mock_response.results.channels = [] # Empty channels
        mock_deepgram.listen.prerecorded.v.return_value.transcribe_file.return_value = mock_response
        
        # Mock built-in open and os functions for file validation
        with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"audio data")))))), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            result = transcribe_audio_deepgram("dummy_path.mp3")
            assert result is None

def test_transcribe_audio_deepgram_no_key():
    from src.monitor import transcribe_audio_deepgram
    from src.config import Config
    original_key = Config.DEEPGRAM_KEY
    Config.DEEPGRAM_KEY = None
    try:
        # Mocking sys.modules['deepgram'] to avoid import error even if it reaches that line
        with patch.dict('sys.modules', {'deepgram': MagicMock()}):
            # Should return None before even trying to import deepgram
            result = transcribe_audio_deepgram("dummy_path")
            assert result is None
    finally:
        Config.DEEPGRAM_KEY = original_key

def test_fetch_transcript_strips_whitespace():
    """fetch_transcript should strip whitespace from Phase 2 results."""
    from src.monitor import fetch_transcript
    with patch('src.monitor.YouTubeTranscriptApi') as mock_api_class:
        mock_api_instance = mock_api_class.return_value
        mock_api_instance.fetch.side_effect = Exception("Phase 1 Failed")
        
        with patch('src.monitor.download_audio') as mock_download, \
             patch('src.monitor.transcribe_audio_deepgram') as mock_transcribe, \
             patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            
            mock_download.return_value = "/tmp/temp_audio.mp3"
            mock_transcribe.return_value = "  Valid transcript with spaces  "
            mock_exists.return_value = True
            
            result = fetch_transcript("test_video")
            assert result == "Valid transcript with spaces"

def test_download_audio_ffmpeg_missing():
    """Verify that when ffmpeg is missing, download_audio omits postprocessors."""
    from src.monitor import download_audio
    with patch('shutil.which', return_value=None) as mock_which, \
         patch('yt_dlp.YoutubeDL') as mock_ydl, \
         patch('glob.glob', return_value=["output_path.m4a"]), \
         patch('os.path.getsize', return_value=50000):
        
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        result = download_audio("video123", "output_path")
        
        # Verify shutil.which was called to check for ffmpeg
        mock_which.assert_called_with("ffmpeg")
        
        # Verify YoutubeDL was instantiated without postprocessors
        called_opts = mock_ydl.call_args[0][0]
        assert 'postprocessors' not in called_opts
        assert result == "output_path.m4a"

def test_download_audio_ffmpeg_present():
    """Verify that when ffmpeg is present, download_audio includes postprocessors."""
    from src.monitor import download_audio
    with patch('shutil.which', return_value="/usr/bin/ffmpeg") as mock_which, \
         patch('yt_dlp.YoutubeDL') as mock_ydl, \
         patch('glob.glob', return_value=["output_path.mp3"]), \
         patch('os.path.getsize', return_value=50000):
        
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        result = download_audio("video123", "output_path")
        
        called_opts = mock_ydl.call_args[0][0]
        assert 'postprocessors' in called_opts
        assert called_opts['postprocessors'][0]['key'] == 'FFmpegExtractAudio'
        assert result == "output_path.mp3"


