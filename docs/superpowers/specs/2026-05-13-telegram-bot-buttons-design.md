# Design: Implement Approve/Reject Buttons in Telegram Bot

## 1. Overview
The Telegram bot currently has a single "GO" button for approvals. We want to add a "Reject" button and improve the feedback loop. We also want to ensure that long-running production tasks don't block the bot's ability to respond to other users or interactions.

## 2. Architecture & Data Flow

### 2.1 UI Components (Telegram Keyboard)
- **Approve Button:**
  - Label: `✅ Approve`
  - Callback Data: `approve|<video_id>`
- **Reject Button:**
  - Label: `❌ Reject`
  - Callback Data: `reject|<video_id>`

### 2.2 Callback Handling
- **`handle_callback` (async):**
  - Extracts action (`approve` or `reject`) and `video_id` from callback data.
  - Answers the callback query immediately to stop the "spinning" indicator in Telegram.
  - **On Approve:**
    - Updates the message text to "✅ *Approved:* Starting Production...".
    - Offloads `process_short_approval` to a separate thread to avoid blocking the event loop.
  - **On Reject:**
    - Updates the message text to "🗑️ *Recommendation Discarded.*".
    - No further action (recommendation remains "seen" in `seen_videos.json` but is ignored for production).

### 2.3 Non-blocking Production
- We will use `asyncio.to_thread()` or `concurrent.futures.ThreadPoolExecutor` to run `process_short_approval`. Since `python-telegram-bot` is async, `asyncio.to_thread()` is the preferred modern approach for running blocking IO-bound code.

## 3. Error Handling
- If `process_short_approval` fails, we will catch the exception in the worker thread.
- We should ideally notify the user if production fails, but for this first step, we will log the error. (Future improvement: update the message text with the error).

## 4. Testing Strategy
- Manual testing by triggering recommendations and clicking both buttons.
- Verify that clicking "Approve" starts the production process (check logs/output).
- Verify that clicking "Reject" simply updates the message text.
- Verify that the bot remains responsive while production is running.
