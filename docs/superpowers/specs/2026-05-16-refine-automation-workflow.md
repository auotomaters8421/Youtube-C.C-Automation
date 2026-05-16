# YouTube Shorts Reframer Refactor Design

> **Status:** Draft
> **Date:** 2026-05-16
> **Goal:** Enhance Telegram interaction and optimize production efficiency by focusing on Viral content.

## 1. Overview
The current system generates both Standard and Viral versions of scripts and audio. This refactor introduces an "Approve/Reject" workflow and prioritizes the "Viral" version for audio generation to save tokens and time.

## 2. Requirements

### A. Telegram UI
- Replace "GO" button with `✅ Approve` and `❌ Reject`.
- **Approval:** Triggers a "Done" notification and starts production.
- **Rejection:** Discards the recommendation.
- **Feedback:** Provide immediate visual confirmation ("Done!") when a button is clicked.

### B. Production Logic (Orchestrator)
- Fetch and reframe transcript via Gemini.
- **Script Scaling:**
    - Source ~100 words -> 30-40 sec output (75-100 words).
    - Source 300+ words -> Max 250-300 words output (~110 sec).
- **TTS Generation:** ONLY generate the MP3 for the `viral_version`.
- **Delivery:** Send both `scripts.json` AND the `viral_version` MP3 to Telegram.

### C. Prompt Engineering (Systemprompt.md)
- Update word count targets in Layer 2C.
- Ensure the `viral_version` focuses on high-impact hooks and the requested durations.

## 3. Component Updates

### 1. `src/telegram_bot.py`
- Update `send_approval_request` to include `callback_data="approve|{id}"` and `callback_data="reject|{id}"`.
- Update `handle_callback` to:
    - Answer with "Done!".
    - On approval: Trigger `process_short_approval`.
    - On rejection: Clear the message.

### 2. `src/orchestrator.py`
- Modify `process_short_approval` to skip TTS for `standard_version`.
- Ensure `send_audio` is called specifically for the viral MP3.

### 3. `docs/superpowers/specs/Systemprompt.md`
- Revise the scaling table to match the new duration requirements.

## 4. Success Criteria
- User clicks "Approve" and sees "Done!".
- A few minutes later, user receives `scripts.json` and ONE MP3 (Viral).
- MP3 duration matches the source-length logic (30-40s for short videos).
