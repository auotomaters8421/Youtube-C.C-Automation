# YouTube Shorts Automation: Full Flow Lockdown (Trial Run)

This document maps the precise end-to-end flow of a single trial run for the YouTube Shorts Reframing Automation. This serves as the "Lockdown" reference for testing and validation.

## Stage 1: Discovery & Monitoring
- **Trigger:** System starts or `watcher.py` detects a change.
- **Process:**
    - `monitor.py` fetches the RSS feed for each channel in `Config.CHANNELS`.
    - Retrieves metadata for each video (title, view count, publish date).
    - Filters for YouTube Shorts specifically.
- **Data Point:** A list of recent Shorts metadata.

## Stage 2: Selection & Ranking
- **Process:**
    - `selector.py` calculates the **View Velocity** for each video: `views / (current_time - upload_time)`.
    - Videos are ranked in descending order of velocity.
    - The top 5 recommendations are identified.
- **Data Point:** `ranked_shorts` list.

## Stage 3: Approval Workflow (Telegram)
- **Action:** `telegram_bot.py` sends an approval request for the top video(s).
- **Interface:** Message contains video title, view count, link, and two buttons: `✅ Approve` and `❌ Reject`.
- **User Interaction:** User clicks `✅ Approve`.
- **Immediate Response:** 
    - Bot calls `query.answer(text="🚀 Done! Production started.")` (pop-up).
    - Bot updates message text to: `✅ Approved: Starting Production for [VideoID]...`.

## Stage 4: Transcription & Reframing
- **Process:**
    - `orchestrator.py` triggers `fetch_transcript(video_id)`.
    - Transcript is passed to `reframe_transcript(transcript)` via Gemini.
- **Reframing Logic (Gemini):**
    - **Scaling:**
        - ~100 words -> 30-40 sec output (75-100 words).
        - 300+ words -> Max 250-300 words (~110 sec).
    - **Output:** A JSON object containing `viral_version` and `standard_version`.

## Stage 5: Audio Generation (Viral Only)
- **Process:**
    - System extracts `hook`, `body`, and `cta` from the `viral_version`.
    - Calls `audio.py:generate_tts()` using Inworld AI.
    - **Optimization:** Skips TTS for `standard_version`.
- **File Output:** `audio_viral_version.mp3`.

## Stage 6: Final Delivery
- **Process:**
    - `telegram_bot.py` sends a completion message: `✅ Production completed for: [Title]`.
    - Sends `scripts.json` (containing both script versions).
    - Sends `audio_viral_version.mp3`.
- **Cleanup:** Files are stored in a timestamped folder in `output/`.

## Lockdown Validation Criteria (Trial Run)
1.  **Approval Check:** Automation must NOT start until `✅ Approve` is clicked.
2.  **Feedback Check:** User must see "Done!" immediately.
3.  **Token Check:** Only ONE Inworld TTS call must be made (Viral).
4.  **Scaling Check:** The MP3 duration must match the scaling rules (e.g., 30-40s for short inputs).
5.  **Delivery Check:** User must receive BOTH the JSON and the MP3.
