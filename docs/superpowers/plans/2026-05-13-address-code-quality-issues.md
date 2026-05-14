# Address Code Quality Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address code quality issues found in the previous task: pin versions in `requirements.txt`, add type hints and validation to `src/config.py`.

**Architecture:** Surgical updates to `requirements.txt` and `src/config.py`.

**Tech Stack:** Python, pip.

---

### Task 1: Pin versions in `requirements.txt`

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Update `requirements.txt` with pinned versions**

```text
google-generativeai==0.8.3
feedparser==6.0.12
requests==2.32.5
python-dotenv==1.0.1
pytest==8.3.3
youtube-transcript-api==1.2.4
```
*(Note: removed unused `schedule` as it is not installed and not used in the codebase)*

- [ ] **Step 2: Commit changes**

```bash
git add requirements.txt
git commit -m "chore: pin dependency versions and remove unused schedule"
```

### Task 2: Add type hints and validation to `src/config.py`

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Add type hints and validation to `Config` class**

```python
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Config:
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    INWORLD_KEY: Optional[str] = os.getenv("INWORLD_KEY")
    INWORLD_SECRET: Optional[str] = os.getenv("INWORLD_SECRET")
    PEXELS_API_KEY: Optional[str] = os.getenv("PEXELS_API_KEY")
    POLLINATIONS_API_KEY: Optional[str] = os.getenv("POLLINATIONS_API_KEY")
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    CHANNELS: List[str] = os.getenv("CHANNELS", "").split(",") if os.getenv("CHANNELS") else []
    OUTPUT_DIR: str = "output"

    # Shorts Reframer Config
    INWORLD_VOICE_ID: str = os.getenv("INWORLD_VOICE_ID", "default-d010pwu587xlzwrg_tencw__my_voice")
    INWORLD_FALLBACK_VOICE: str = os.getenv("INWORLD_FALLBACK_VOICE", "Alex")
    GEMINI_SYSTEM_PROMPT: str = os.getenv("GEMINI_SYSTEM_PROMPT", "Reframe the following YouTube Short transcript into a controversial, problem-solving script. Focus on a heavy hook in the first 3 seconds.")

    @classmethod
    def validate(cls):
        """
        Validates that all mandatory configuration keys are present.
        """
        mandatory_keys = [
            "GEMINI_API_KEY",
            "INWORLD_KEY",
            "INWORLD_SECRET",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID"
        ]
        missing = [key for key in mandatory_keys if not getattr(cls, key)]
        if missing:
            # We log a warning instead of raising an error to allow partial configuration for tests/specific runs
            import logging
            logging.warning(f"Missing mandatory configuration keys: {', '.join(missing)}")
```

- [ ] **Step 2: Commit changes**

```bash
git add src/config.py
git commit -m "refactor: add type hints and validation to Config"
```

### Task 3: Final Verification

- [ ] **Step 1: Run tests to ensure no regressions**

Run: `pytest`
Expected: All tests pass.

- [ ] **Step 2: Verify `Config.validate()` can be called (optional check)**

Run a small script to call `Config.validate()` and ensure it doesn't crash.

```python
from src.config import Config
Config.validate()
print("Config validation passed (or warned).")
```

- [ ] **Step 3: DONE**
