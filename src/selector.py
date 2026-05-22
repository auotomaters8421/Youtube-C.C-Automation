import json
import time
import logging
import google.generativeai as genai
from src.config import Config

# Configure Gemini at module load if key is present
if hasattr(Config, 'GEMINI_API_KEY') and Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)


def select_topic(videos):
    """
    Analyzes a list of YouTube videos and picks the most viral topic using Gemini.
    """
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
    prompt = f"Analyze these YouTube videos and pick the most viral topic for an AI automation niche: {videos}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "New AI Automation Trends"  # Fallback


def rank_shorts(shorts_data):
    """
    Ranks Shorts based on view velocity: views / (current_time - upload_time).
    """
    current_time = time.time()

    for short in shorts_data:
        age = current_time - short.get('upload_time', 0)
        # Minimum age of 1 second to avoid division by zero or inflated velocity
        age = max(age, 1)
        short['velocity'] = short.get('views', 0) / age

    # Sort by velocity descending
    return sorted(shorts_data, key=lambda x: x['velocity'], reverse=True)


def reframe_transcript(transcript, content_type="auto"):
    """
    Reframes a YouTube Short transcript using Gemini Pro based on the detailed system prompt.
    Returns a dictionary with viral_version and standard_version.
    """
    model = genai.GenerativeModel(
        model_name=Config.GEMINI_MODEL,
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
        logging.error(f"Gemini Reframing Error: {e}")
        # Structured fallback so callers always get the expected shape
        return {
            "error": str(e),
            "viral_version": {"hook": "", "body": transcript, "cta": ""},
            "standard_version": {"hook": "", "body": transcript, "cta": ""}
        }


def reframe_as_inspiration(transcript):
    """
    Clones a YouTube Short transcript as creative inspiration.

    Keeps the SAME topic and factual content but writes a BETTER version
    using Gemini Pro with completely different psychological hooks, a stronger opening 3 seconds,
    and upgraded persuasion techniques.

    Returns a dict with viral_version, standard_version,
    psychological_techniques_used, and inspiration_mode=True.
    """
    model = genai.GenerativeModel(
        model_name=Config.GEMINI_MODEL,
        system_instruction=Config.get_gemini_system_prompt()
    )

    inspiration_prompt = f"""You are an elite YouTube Shorts copywriter specialising in psychological persuasion.

A user has sent you a transcript from a high-performing YouTube Short as INSPIRATION.
Your job is to write a SIGNIFICANTLY BETTER version that:

1. Covers the EXACT SAME topic and factual information as the original
2. Uses COMPLETELY DIFFERENT psychological hooks — choose from:
   - Curiosity gap ("What nobody tells you about...")
   - Fear of missing out ("If you don't know this yet, you're already behind")
   - Social proof + contrast ("Top creators do this, average ones don't")
   - Shock/surprise opener (lead with the single most surprising fact)
   - Identity challenge ("You think you know X? Think again")
   - Future pacing ("In 60 seconds, you'll never look at X the same way")
3. Has a more compelling, scroll-stopping opening 3 seconds
4. Is more emotionally engaging and psychologically triggering throughout
5. Ends with a stronger, curiosity-driven CTA that makes viewers want more

INSPIRATION TRANSCRIPT:
{transcript}

Return ONLY valid JSON with this exact structure:
{{
  "viral_version": {{
    "hook": "<punchy 1-2 sentence opener — the first 3 seconds>",
    "body": "<the main content, rewritten with the new psychological frame>",
    "cta": "<a curiosity-driven call to action>"
  }},
  "standard_version": {{
    "hook": "<a calmer but still engaging opener>",
    "body": "<the same content, slightly less aggressive tone>",
    "cta": "<a clear, direct call to action>"
  }},
  "psychological_techniques_used": "<comma-separated list of techniques applied>",
  "inspiration_mode": true
}}"""

    try:
        response = model.generate_content(
            inspiration_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"Gemini Inspiration Reframing Error: {e}")
        return {
            "error": str(e),
            "viral_version": {"hook": "", "body": transcript, "cta": ""},
            "standard_version": {"hook": "", "body": transcript, "cta": ""},
            "psychological_techniques_used": "",
            "inspiration_mode": True
        }
