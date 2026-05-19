# Deepgram Fallback Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fallback transcription system using Deepgram and `yt-dlp` for YouTube Shorts that lack captions.

**Architecture:** Update `fetch_transcript` to attempt `youtube-transcript-api` first. On failure, download audio via `yt-dlp`, transcribe via Deepgram API, and delete the audio file immediately. Includes runtime key updates via Telegram.

**Tech Stack:** `yt-dlp`, `deepgram-sdk`, `python-dotenv`, `python-telegram-bot`.

---

### Task 1: Update Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add new libraries to requirements.txt**

Add `yt-dlp` and `deepgram-sdk` to the end of the file.

```text
yt-dlp==2024.5.26
deepgram-sdk==3.3.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "build: add yt-dlp and deepgram-sdk dependencies"
```

---

### Task 2: Configuration & Runtime Updates

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Add DEEPGRAM_KEY to Config class**

```python
class Config:
    # ... existing keys ...
    DEEPGRAM_KEY: Optional[str] = os.getenv("DEEPGRAM_KEY")
```

- [ ] **Step 2: Add validation for DEEPGRAM_KEY (Optional warning)**

Update `validate()` method to include `DEEPGRAM_KEY` in the warning if missing.

- [ ] **Step 3: Commit**

```bash
git add src/config.py
git commit -m "config: add DEEPGRAM_KEY to Config"
```

---

### Task 3: Telegram Command for Key Update

**Files:**
- Modify: `src/telegram_bot.py`

- [ ] **Step 1: Implement `/update_deepgram_key` handler**

```python
async def update_deepgram_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /update_deepgram_key <key>")
        return
    new_key = context.args[0]
    Config.update_runtime_config("DEEPGRAM_KEY", new_key)
    await update.message.reply_text("✅ Deepgram API Key updated for this session.")
```

- [ ] **Step 2: Register the command in `start_bot`**

```python
application.add_handler(CommandHandler("update_deepgram_key", update_deepgram_key))
```

- [ ] **Step 3: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: add /update_deepgram_key command"
```

---

### Task 4: Audio Download and Transcription Logic

**Files:**
- Modify: `src/monitor.py`

- [ ] **Step 1: Import Deepgram and yt-dlp**

```python
import os
import yt_dlp
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)
```

- [ ] **Step 2: Implement `download_audio` helper**

```python
def download_audio(video_id, output_path):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return f"{output_path}.m4a"
```

- [ ] **Step 3: Implement `transcribe_audio_deepgram` helper**

```python
def transcribe_audio_deepgram(audio_path):
    if not Config.DEEPGRAM_KEY:
        return None
    
    try:
        deepgram = DeepgramClient(Config.DEEPGRAM_KEY)
        with open(audio_path, "rb") as file:
            buffer_data = file.read()
        
        payload: FileSource = {"buffer": buffer_data}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )
        
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        return response.results.channels[0].alternatives[0].transcript
    except Exception as e:
        import logging
        logging.error(f"Deepgram Error: {e}")
        return None
```

- [ ] **Step 4: Commit**

```bash
git add src/monitor.py
git commit -m "feat: implement audio download and deepgram transcription helpers"
```

---

### Task 5: Integrate Fallback in `fetch_transcript`

**Files:**
- Modify: `src/monitor.py`

- [ ] **Step 1: Update `fetch_transcript` to use fallback**

```python
def fetch_transcript(video_id):
    # Try Phase 1: Free API
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        return " ".join([snippet['text'] for snippet in transcript_list])
    except Exception as e:
        import logging
        logging.info(f"Phase 1 transcript fetch failed for {video_id}: {e}. Trying Phase 2 (Deepgram)...")

    # Try Phase 2: Deepgram Fallback
    audio_base = os.path.join("/tmp", f"temp_audio_{video_id}")
    audio_path = None
    try:
        audio_path = download_audio(video_id, audio_base)
        transcript = transcribe_audio_deepgram(audio_path)
        return transcript
    except Exception as fallback_err:
        import logging
        logging.error(f"Phase 2 transcript fetch failed for {video_id}: {fallback_err}")
        return None
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
```

- [ ] **Step 2: Commit**

```bash
git add src/monitor.py
git commit -m "feat: integrate Deepgram fallback into fetch_transcript"
```

---

### Task 6: Verification and Alerts

**Files:**
- Modify: `src/orchestrator.py` (Optional: verify existing alert works)

- [ ] **Step 1: Verify Telegram Notification**

Ensure `process_short_approval` correctly sends the "No transcript found" message if both phases fail. (Existing code should already do this).

- [ ] **Step 2: Test with a Short known to have no captions**

Run: `python main.py` (Manually trigger a video without captions or use a test script).

- [ ] **Step 3: Final Commit**

```bash
git commit --allow-empty -m "fix: finalize Deepgram integration and verification"
```
