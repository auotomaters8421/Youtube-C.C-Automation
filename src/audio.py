import requests
import base64
from src.config import Config

class InworldCreditError(Exception):
    """Exception raised when Inworld AI credits are exhausted or billing issues occur."""
    pass

def generate_tts(text, filename):
    """
    Generates text-to-speech using Inworld AI REST API (2026).
    """
    import base64
    # The Inworld REST API typically uses Basic auth with base64(apiKey:apiSecret)
    key = Config.INWORLD_KEY
    secret = Config.INWORLD_SECRET
    
    if secret:
        auth_str = base64.b64encode(f"{key}:{secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Content-Type": "application/json"
        }
    else:
        # Fallback to key-only if secret is missing (though likely incorrect)
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
            
            # Detect Credit/Billing Exhaustion
            if response.status_code in [402, 429]:
                error_msg = f"Inworld Credit Exhausted (Status {response.status_code}): {response.text}"
                print(error_msg)
                raise InworldCreditError(error_msg)
            
            if response.status_code == 403:
                print(f"Inworld 403 Forbidden with voice {voice}. Check credentials.")
                if voice == Config.INWORLD_FALLBACK_VOICE:
                    raise Exception("Inworld 403 Forbidden: Check if your API Key has TTS permissions and that it is the correct key format.")
                continue
            
            response.raise_for_status()
            
            # In the 2026 REST API, the audio is returned as a base64 string in 'audioContent'
            data = response.json()
            audio_content = data.get("audioContent")
            
            if not audio_content:
                print(f"Warning: No audioContent in response for voice {voice}")
                if voice == Config.INWORLD_FALLBACK_VOICE:
                    raise Exception("Inworld API response did not contain 'audioContent'.")
                continue
                
            with open(filename, "wb") as f:
                f.write(base64.b64decode(audio_content))
            
            print(f"Successfully generated TTS: {filename}")
            return filename
        except Exception as e:
            if voice == Config.INWORLD_FALLBACK_VOICE:
                print(f"Failed to generate TTS with fallback voice '{voice}': {e}")
                raise e
            print(f"Failed to generate TTS with primary voice '{voice}': {e}. Attempting fallback...")

