import pytest
from unittest.mock import patch, MagicMock
import os
import requests

def test_generate_tts_success(monkeypatch):
    # Mocking environment variables for Config
    monkeypatch.setenv("INWORLD_KEY", "test_key")
    monkeypatch.setenv("INWORLD_SECRET", "test_secret")
    
    # We need to reload src.config if it's already imported, 
    # but since this is a new test run, it should be fine if we import it inside.
    import src.config
    import src.audio
    import importlib
    importlib.reload(src.config)
    importlib.reload(src.audio)
    
    from src.audio import generate_tts
    import base64
    
    fake_audio_b64 = base64.b64encode(b"fake audio content").decode("utf-8")
    mock_response = MagicMock()
    mock_response.json.return_value = {"audioContent": fake_audio_b64}
    mock_response.status_code = 200
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        filename = "test_audio.mp3"
        result = generate_tts("Hello world", filename)
        
        assert result == filename
        assert os.path.exists(filename)
        
        # Verify mock_post was called with expected arguments
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.inworld.ai/tts/v1/voice"
        
        expected_payload = {
            "text": "Hello world",
            "voiceId": "default-d010pwu587xlzwrg_tencw__my_voice",
            "modelId": "inworld-tts-1.5-max",
            "audioConfig": {
                "audioEncoding": "MP3"
            }
        }
        assert kwargs["json"] == expected_payload
        assert "Authorization" in kwargs["headers"]
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

def test_generate_tts_fallback(monkeypatch):
    monkeypatch.setenv("INWORLD_VOICE_ID", "custom_voice")
    monkeypatch.setenv("INWORLD_FALLBACK_VOICE", "fallback_voice")
    
    import src.config
    import src.audio
    import importlib
    importlib.reload(src.config)
    importlib.reload(src.audio)
    
    from src.audio import generate_tts
    import base64
    
    # First call fails (e.g. 400 Bad Request because voiceId is invalid)
    # Second call succeeds
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 400
    mock_response_fail.raise_for_status.side_effect = requests.HTTPError("Bad Request")
    
    fake_audio_b64 = base64.b64encode(b"fallback audio").decode("utf-8")
    mock_response_ok = MagicMock()
    mock_response_ok.json.return_value = {"audioContent": fake_audio_b64}
    mock_response_ok.status_code = 200
    
    with patch("requests.post", side_effect=[mock_response_fail, mock_response_ok]) as mock_post:
        filename = "test_fallback.mp3"
        result = generate_tts("Hello fallback", filename)
        
        assert result == filename
        assert os.path.exists(filename)
        assert mock_post.call_count == 2
        
        # Verify first call used primary voice
        args1, kwargs1 = mock_post.call_args_list[0]
        assert kwargs1["json"]["voiceId"] == "custom_voice"
        
        # Verify second call used fallback voice
        args2, kwargs2 = mock_post.call_args_list[1]
        assert kwargs2["json"]["voiceId"] == "fallback_voice"
        
        if os.path.exists(filename):
            os.remove(filename)

def test_generate_tts_import_error():
    # This is to ensure the file exists and can be imported
    try:
        from src.audio import generate_tts
    except ImportError:
        pytest.fail("Could not import generate_tts from src.audio")
