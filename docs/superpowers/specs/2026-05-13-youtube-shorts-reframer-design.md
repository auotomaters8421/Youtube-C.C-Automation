# YouTube Shorts Reframing Automation Design

> **Status:** Approved by User
> **Date:** 2026-05-13
> **Goal:** Transform high-performing YouTube Shorts into reframed audio-only content using Gemini and Inworld AI.

## 1. Overview
This system monitors specific YouTube channels for high-velocity Shorts. It analyzes performance metrics, requests user approval via Telegram, fetches transcripts, reframes them into controversial/problem-solving scripts via Gemini, and generates high-quality voiceovers via Inworld AI. All video and image generation is removed.

## 2. Architecture

### A. Core Modules
1.  **Monitor (Shorts Analyzer):**
    *   Fetches RSS feeds.
    *   Retrieves metadata (views, duration, likes, upload date) for each Short.
    *   Calculates "Velocity": `views / (current_time - upload_time)`.
2.  **Selector (Ranking Engine):**
    *   Ranks Shorts based on Velocity (Primary) and Engagement (Secondary).
    *   Filters for Shorts with transcripts available (or notifies if high engagement).
3.  **Telegram Approval Bot:**
    *   Sends recommended Shorts to the user with a "GO" button.
    *   Handles the "GO" callback to trigger processing.
4.  **Reframer (Gemini 2.0 Flash):**
    *   Uses a strict (placeholder) system prompt to reframe 200-word transcripts.
    *   Focus: Controversial, hook-heavy, problem-solving.
5.  **Audio Generator (Inworld AI):**
    *   Produces voiceovers using Voice ID: `default-d010pwu587xlzwrg_tencw__my_voice`.
    *   Fallback voice: `Alex`.
    *   Removes all other asset generation (images/video).

### B. Tech Stack
*   **Language:** Python 3.10+
*   **LLM:** Gemini 2.0 Flash
*   **TTS:** Inworld AI (REST API)
*   **Transcript Fetching:** `youtube-transcript-api`
*   **Telegram:** `python-telegram-bot`

## 3. Data Flow
1.  **Discovery:** Watcher identifies new Shorts via RSS.
2.  **Analysis:** System fetches metrics and calculates ranking.
3.  **Approval:** "Top Recommended" Short sent to Telegram. User clicks "GO".
4.  **Transcription:** System fetches the transcript.
5.  **Reframing:** Gemini reframes the transcript into a new script.
6.  **Voiceover:** Inworld AI generates the audio file.
7.  **Delivery:** Final audio file saved in a timestamped folder.

## 4. Reframing Logic (Placeholder)
The system will use a prompt like:
`"Reframe the following YouTube Short transcript into a controversial, problem-solving script. Focus on a heavy hook in the first 3 seconds. Transcript: [TEXT]"`

## 5. Success Criteria
*   Correct identification of high-velocity Shorts.
*   Reliable transcript fetching and reframing.
*   Seamless Telegram approval workflow.
*   High-quality audio output using the specified Inworld voice.
*   Zero calls to image or video generation services.
