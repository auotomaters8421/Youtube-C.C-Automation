import requests
import base64
from src.config import Config

def generate_tts(text, filename):
    """
    Generates text-to-speech using Inworld AI REST API (2026).
    """
    # The Inworld REST API uses the key directly with 'Basic' auth.
    key = Config.INWORLD_KEY
    
    headers = {
        "Authorization": f"Basic {key}",
        "Content-Type": "application/json"
    }
    
    voices = [Config.INWORLD_VOICE_ID, Config.INWORLD_FALLBACK_VOICE]
    
    for voice in voices:
        payload = {
            "text": text,
            "voiceId": voice,
            "modelId": "inworld-tts-1.5-max",
            "audioConfig": {
                "audioEncoding": "MP3"
            }
        }
        
        print(f"Requesting TTS from Inworld with voice '{voice}' for: {text[:30]}...")
        try:
            response = requests.post("https://api.inworld.ai/tts/v1/voice", json=payload, headers=headers)
            
            if response.status_code == 403:
                raise Exception("Inworld 403 Forbidden: Check if your API Key has TTS permissions and that it is the correct key format.")
            
            response.raise_for_status()
            
            # In the 2026 REST API, the audio is returned as a base64 string in 'audioContent'
            data = response.json()
            audio_content = data.get("audioContent")
            
            if not audio_content:
                raise Exception("Inworld API response did not contain 'audioContent'.")
                
            with open(filename, "wb") as f:
                f.write(base64.b64decode(audio_content))
            
            return filename
        except Exception as e:
            if voice == Config.INWORLD_FALLBACK_VOICE:
                print(f"Failed to generate TTS with fallback voice '{voice}': {e}")
                raise e
            print(f"Failed to generate TTS with primary voice '{voice}': {e}. Attempting fallback...")

