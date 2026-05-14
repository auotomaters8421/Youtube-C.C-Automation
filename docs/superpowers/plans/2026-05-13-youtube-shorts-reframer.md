# YouTube Shorts Reframer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform high-performing YouTube Shorts into reframed audio-only content using Gemini and Inworld AI.

**Architecture:** A Python-based pipeline that monitors RSS feeds, calculates "Velocity" (views/time), requests Telegram approval, reframes transcripts using Gemini, and generates audio via Inworld AI.

**Tech Stack:** Python 3.10+, Gemini 2.0 Flash, Inworld AI REST API, `youtube-transcript-api`, `python-telegram-bot`.

---

### Task 1: Environment & Config Setup

**Files:**
- Modify: `requirements.txt`
- Modify: `src/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add `youtube-transcript-api` to requirements**

```text
youtube-transcript-api
```

- [ ] **Step 2: Run install**

Run: `pip install youtube-transcript-api`

- [ ] **Step 3: Update Config class**

```python
class Config:
    # ... existing ...
    INWORLD_VOICE_ID = os.getenv("INWORLD_VOICE_ID", "default-d010pwu587xlzwrg_tencw__my_voice")
    INWORLD_FALLBACK_VOICE = os.getenv("INWORLD_FALLBACK_VOICE", "Alex")
    GEMINI_SYSTEM_PROMPT = os.getenv("GEMINI_SYSTEM_PROMPT", "Reframe the following YouTube Short transcript into a controversial, problem-solving script. Focus on a heavy hook in the first 3 seconds.")
```

- [ ] **Step 4: Update `.env.example`**

```text
INWORLD_VOICE_ID=default-d010pwu587xlzwrg_tencw__my_voice
INWORLD_FALLBACK_VOICE=Alex
GEMINI_SYSTEM_PROMPT="Reframe the following YouTube Short transcript into a controversial, problem-solving script..."
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/config.py .env.example
git commit -m "chore: setup dependencies and config for shorts reframer"
```

---

### Task 2: Monitor Enhancement (Metrics & Transcripts)

**Files:**
- Modify: `src/monitor.py`
- Test: `tests/test_monitor.py`

- [ ] **Step 1: Add transcript and metrics fetching to `src/monitor.py`**

```python
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import time

def fetch_video_metrics(video_id):
    """
    Fetches views, duration, and upload date for a video.
    Note: Requires a scraper or YouTube Data API. For now, we'll use a simplified scraper approach.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    # Simple regex extraction for demo/minimal implementation
    import re
    views_match = re.search(r'\"viewCount\":\"(\d+)\"', response.text)
    views = int(views_match.group(1)) if views_match else 0
    return {"views": views, "timestamp": time.time()}

def fetch_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in transcript_list])
    except Exception as e:
        print(f"Transcript Error: {e}")
        return None
```

- [ ] **Step 2: Write test for transcript fetching**

```python
def test_fetch_transcript_not_found():
    from src.monitor import fetch_transcript
    assert fetch_transcript("invalid_id") is None
```

- [ ] **Step 3: Commit**

```bash
git add src/monitor.py tests/test_monitor.py
git commit -m "feat: add transcript and metrics fetching to monitor"
```

---

### Task 3: Selection Logic (Velocity Ranking)

**Files:**
- Modify: `src/selector.py`
- Test: `tests/test_selector.py`

- [ ] **Step 1: Implement `rank_shorts` in `src/selector.py`**

```python
def rank_shorts(shorts_data):
    """
    Ranks shorts by velocity: views / (current_time - upload_time).
    shorts_data: list of dicts {video_id, title, views, upload_time}
    """
    now = time.time()
    for short in shorts_data:
        age = max(now - short['upload_time'], 1) # Avoid division by zero
        short['velocity'] = short['views'] / age
    
    return sorted(shorts_data, key=lambda x: x['velocity'], reverse=True)
```

- [ ] **Step 2: Write test for ranking**

```python
def test_rank_shorts():
    from src.selector import rank_shorts
    data = [
        {'title': 'Old Viral', 'views': 1000000, 'upload_time': 0},
        {'title': 'New Viral', 'views': 100000, 'upload_time': time.time() - 3600}
    ]
    ranked = rank_shorts(data)
    assert ranked[0]['title'] == 'New Viral'
```

- [ ] **Step 3: Commit**

```bash
git add src/selector.py tests/test_selector.py
git commit -m "feat: implement velocity-based ranking"
```

---

### Task 4: Gemini Reframer

**Files:**
- Modify: `src/selector.py`

- [ ] **Step 1: Implement `reframe_transcript`**

```python
def reframe_transcript(transcript):
    model = genai.GenerativeModel('gemini-2.0-flash')
    system_prompt = Config.GEMINI_SYSTEM_PROMPT
    prompt = f"{system_prompt}\n\nTranscript:\n{transcript}"
    
    response = model.generate_content(prompt)
    return response.text
```

- [ ] **Step 2: Commit**

```bash
git add src/selector.py
git commit -m "feat: implement Gemini reframing logic"
```

---

### Task 5: TTS Voice Update

**Files:**
- Modify: `src/audio.py`

- [ ] **Step 1: Update `generate_tts` to use configured voice**

```python
def generate_tts(text, filename):
    # ...
    payload = {
        "text": text,
        "voiceId": Config.INWORLD_VOICE_ID,
        "modelId": "inworld-tts-1.5-max",
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }
    # ...
```

- [ ] **Step 2: Commit**

```bash
git add src/audio.py
git commit -m "feat: update TTS to use specific Inworld voice"
```

---

### Task 6: Telegram Approval Flow

**Files:**
- Modify: `src/telegram_bot.py`
- Modify: `src/orchestrator.py`

- [ ] **Step 1: Update Telegram bot to handle "GO" for a specific video ID**

```python
# In src/telegram_bot.py (pseudo-code/concept)
# Use InlineKeyboardButton with callback_data="go_<video_id>"
```

- [ ] **Step 2: Refactor `orchestrator.py` to handle the new flow**

```python
def process_short(video_id):
    transcript = fetch_transcript(video_id)
    if not transcript:
        # Handle notification logic
        return
    
    new_script = reframe_transcript(transcript)
    audio_path = generate_tts(new_script, "audio.mp3")
    # Delivery...
```

- [ ] **Step 3: Commit**

```bash
git add src/telegram_bot.py src/orchestrator.py
git commit -m "feat: implement telegram approval and orchestrator refactor"
```

---

### Task 7: Cleanup & Final Wiring

**Files:**
- Delete: `src/assets.py` (if unused)
- Modify: `main.py`

- [ ] **Step 1: Remove `assets.py` from project**

Run: `rm src/assets.py`

- [ ] **Step 2: Final wiring in `main.py`**

- [ ] **Step 3: Commit**

```bash
git add src/ main.py
git commit -m "cleanup: remove image/video generation and final wiring"
```
