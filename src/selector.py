import google.generativeai as genai
from src.config import Config

# Configure Gemini
# Note: In a real environment, this might be called once at app startup
if hasattr(Config, 'GEMINI_API_KEY') and Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)

import time

def select_topic(videos):
    """
    Analyzes a list of YouTube videos and picks the most viral topic using Gemini.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"Analyze these YouTube videos and pick the most viral topic for an AI automation niche: {videos}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "New AI Automation Trends" # Fallback

def rank_shorts(shorts_data):
    """
    Ranks Shorts based on view velocity: views / (current_time - upload_time).
    """
    current_time = time.time()
    
    for short in shorts_data:
        age = current_time - short.get('upload_time', 0)
        # Handle recent uploads with min age of 1 second to avoid division by zero or inflated velocity
        age = max(age, 1)
        short['velocity'] = short.get('views', 0) / age
        
    # Sort by velocity descending
    return sorted(shorts_data, key=lambda x: x['velocity'], reverse=True)

def reframe_transcript(transcript):
    """
    Reframes a YouTube Short transcript using Gemini based on a system prompt.
    """
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=Config.GEMINI_SYSTEM_PROMPT
    )
    
    try:
        response = model.generate_content(transcript)
        return response.text
    except Exception as e:
        print(f"Gemini Reframing Error: {e}")
        return transcript # Fallback to original transcript if reframing fails
