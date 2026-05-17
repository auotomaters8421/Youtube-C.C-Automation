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
    model = genai.GenerativeModel('gemini-1.5-flash')
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

import json

def reframe_transcript(transcript, content_type="auto"):
    """
    Reframes a YouTube Short transcript using Gemini based on the detailed system prompt.
    Returns a dictionary with viral_version and standard_version.
    """
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=Config.get_gemini_system_prompt()
    )
    
    input_block = f"TRANSCRIPT: {transcript}\nCONTENT_TYPE: {content_type}"
    
    try:
        response = model.generate_content(
            input_block,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        import logging
        logging.error(f"Gemini Reframing Error: {e}")
        # Return a structured fallback
        return {
            "error": str(e),
            "viral_version": {"hook": "", "body": transcript, "cta": ""},
            "standard_version": {"hook": "", "body": transcript, "cta": ""}
        }
