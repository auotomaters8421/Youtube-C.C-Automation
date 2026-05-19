# Design Spec: Deepgram Fallback Integration

## Purpose
The current system fails to fetch transcripts for approximately 95% of YouTube Shorts because it relies solely on pre-existing captions. This integration adds a robust fallback: if captions are missing, the system will download the Short's audio and use Deepgram's ASR (Automatic Speech Recognition) to generate a transcript.

## Architecture

### 1. Dual-Phase Transcription
- **Phase 1 (Primary):** Use `youtube-transcript-api`. If a transcript is found, return it immediately (Cost: $0).
- **Phase 2 (Fallback):** If Phase 1 fails or returns no data:
    1. Download the Short's audio using `yt-dlp` (MP3 format, low bitrate to save bandwidth).
    2. Send audio to Deepgram's `nova-2` model via the `deepgram-sdk`.
    3. Cleanup: Immediately delete the local audio file after receiving the API response.
    4. Return the transcribed text.

### 2. Infrastructure & Storage
- **Platform:** Render.
- **Storage Strategy:** "Surgical Download." Audio files are stored in a temporary `/tmp` directory and deleted within the same execution block to maintain compliance with Render's disk limits.
- **Dependencies:** `yt-dlp`, `deepgram-sdk`.

### 3. Monitoring & Management
- **Error Handling:** If Deepgram returns authentication or credit-related errors (401, 403), the system halts production for that video and alerts the user.
- **Telegram Commands:** 
    - `/update_deepgram_key <key>`: Update the `DEEPGRAM_KEY` at runtime without a redeploy.
- **Notifications:** Telegram alert when credits are exhausted or if transcription fails entirely.

## Success Criteria
- [ ] System successfully fetches transcripts for Shorts that have no captions.
- [ ] Disk space usage remains stable (no leftover MP3 files).
- [ ] User can update Deepgram keys via Telegram.
- [ ] $200 credit is consumed only when necessary.
