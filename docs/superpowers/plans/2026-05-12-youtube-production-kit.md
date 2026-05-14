# YouTube Production Kit Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python automation that monitors YouTube RSS feeds, alerts the user via Telegram, and only generates a "Production Kit" folder after receiving a "GO" command.

**Architecture:** 
1.  **Setup Wizard:** CLI for credential collection.
2.  **Watcher:** Background process to detect new uploads.
3.  **Telegram Bot:** Interaction layer for alerts and approval.
4.  **Production Engine:** Modular services for Gemini, Inworld, Pollinations, and Pexels.

**Tech Stack:** Python 3.10+, `python-telegram-bot`, `google-generativeai`, `feedparser`, `requests`, `python-dotenv`.

---

### Task 1: The Setup Wizard (`setup.py`)

**Files:**
- Create: `setup.py`
- Modify: `src/config.py`

- [ ] **Step 1: Implement interactive collection in `setup.py`**
    *   Ask for Gemini Key, Inworld Key/Secret, Pexels Key, Telegram Bot Token, and Chat ID.
    *   Ask for a list of YouTube Channel IDs.
    *   Write to `.env`.

- [ ] **Step 2: Update `src/config.py` to include Telegram credentials**
```python
class Config:
    # ... existing keys ...
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
```

---

### Task 2: RSS Watcher with State

**Files:**
- Create: `src/watcher.py`
- Create: `data/seen_videos.json` (to track processed videos)

- [ ] **Step 1: Implement `src/watcher.py`**
    *   Function to check feeds and compare against `seen_videos.json`.
    *   Return a list of new video titles and IDs.

---

### Task 3: Telegram Interaction Layer

**Files:**
- Create: `src/telegram_bot.py`

- [ ] **Step 1: Implement the Bot listener**
    *   Function `send_alert(video_title)`: Sends the "New Video" message.
    *   Command Handler `/go`: Triggers the production for the last alerted video.
    *   Command Handler `/stop`: Ignores the last alert.

---

### Task 4: Responsive Orchestrator

**Files:**
- Modify: `src/orchestrator.py`

- [ ] **Step 1: Update `run_automation` to accept a specific video ID/Title**
    *   Instead of looping through all channels, it should be callable for a specific event triggered by Telegram.

---

### Task 5: Integration & Final Main Loop

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Connect Watcher and Telegram Bot**
    *   Background thread for RSS Watching.
    *   Main thread for Telegram Bot polling.

---
### Final Review Checklist
1. `setup.py` works for a first-time user? Yes.
2. Telegram bot correctly waits for "GO"? Yes.
3. Production Kit includes all assets and Director's Cut? Yes.
