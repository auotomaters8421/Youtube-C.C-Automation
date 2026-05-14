# YouTube Production Kit Automation Design

> **Status:** Drafted & Approved by User (v2: Telegram-Triggered)
> **Date:** 2026-05-12
> **Goal:** A Python-based automation that transforms YouTube RSS news into a full "Production Kit" folder (Script, Voiceover, and AI/Stock Assets) after user approval via Telegram.

## 1. Overview
This system provides a responsive, user-in-the-loop pipeline. It monitors specific YouTube channels via RSS. When new content is detected, it alerts the user via Telegram and waits for a "GO" command before generating the Production Kit.

## 2. Architecture

### A. Core Modules
1.  **Setup Wizard (`setup.py`):** Interactive CLI to collect and validate API keys and YouTube Channel IDs.
2.  **Monitor (RSS Watcher):** Background process that checks configured feeds every 15-30 minutes.
3.  **Telegram Bot Integration:** 
    *   Sends alerts for new videos.
    *   Listens for "GO" command to trigger generation.
4.  **Selector & Generator (Gemini 3.1 Pro):**
    *   Generates a viral-ready script and "Director's Cut" visual map.
5.  **Audio Generator (Inworld AI):** Produces voiceovers using a cloned voice.
6.  **Asset Sourcing:**
    *   AI Images: Pollinations.ai (Flux).
    *   B-Roll: Pexels API.

### B. Tech Stack
*   **Language:** Python 3.10+
*   **LLM:** Gemini 3.1 Pro
*   **TTS:** Inworld AI
*   **Images:** Pollinations.ai
*   **Video Assets:** Pexels API
*   **Telegram:** `python-telegram-bot` or direct REST calls.

## 3. Data Flow (Option B: Approval Workflow)
1.  **Watcher:** Detects new video ID in RSS.
2.  **Alert:** Sends Telegram message: "🎬 New Video Detected: [Title]. Should I generate the Production Kit? Reply 'GO' to proceed."
3.  **Trigger:** User replies "GO".
4.  **Generation:** Python executes the full pipeline (Gemini -> Inworld -> Pollinations -> Pexels).
5.  **Delivery:** Files organized into `output/[DATE]_[TOPIC]/` and a final confirmation sent to Telegram.

## 4. Director's Cut Specification
The `directors_cut.md` will follow this structure:
| Script Line | Asset Filename | Creative Instruction |
| :--- | :--- | :--- |
| "Nvidia just changed everything..." | `ai_robot_thinking.jpg` | "Start with a fast glitch transition. Slow zoom on the robot's eyes." |
| "The new Blackwell chip is 30x faster." | `pexels_gpu_render.mp4` | "Keep this clip for the full duration of the stat. Use high-energy captions." |

## 5. Success Criteria
*   Successfully generates a folder with all assets in under 5 minutes.
*   Reliably fetches from RSS without hitting YouTube API quotas.
*   Creative instructions in the Director's Cut are "non-generic" and context-aware.
