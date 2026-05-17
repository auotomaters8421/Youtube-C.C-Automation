# Telegram Bot Approve/Reject Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Telegram bot to include Approve/Reject buttons and provide immediate feedback without blocking the bot's responsiveness.

**Architecture:** Update `send_approval_request` for dual buttons. In `handle_callback`, use `asyncio.to_thread` to run the blocking production process. Provide immediate UI feedback using `query.answer` and `query.edit_message_text`.

**Tech Stack:** Python, `python-telegram-bot`, `asyncio`, `requests`.

---

### Task 1: Update Approval Request Keyboard

**Files:**
- Modify: `src/telegram_bot.py`

- [ ] **Step 1: Refactor `send_approval_request` to use Approve and Reject buttons**

```python
def send_approval_request(video):
    """
    Sends an approval request with Approve and Reject buttons for a specific video.
    """
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Telegram configuration missing.")
        return

    video_id = video.get('yt_videoid')
    title = video.get('title')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Dual button keyboard
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve|{video_id}"},
            {"text": "❌ Reject", "callback_data": f"reject|{video_id}"}
        ]]
    }
    
    text = (
        f"🎬 *New Top Recommendation*\n\n"
        f"*Title:* {title}\n"
        f"*Views:* {video.get('views', 0):,}\n"
        f"*Link:* [YouTube](https://youtube.com/watch?{video_id})\n\n"
        f"Would you like to start production?"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Sent approval request for: {title}")
    except Exception as e:
        print(f"Failed to send approval request: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: update telegram approval request with dual buttons"
```

---

### Task 2: Update Callback Handler for Async Feedback

**Files:**
- Modify: `src/telegram_bot.py`

- [ ] **Step 1: Update `handle_callback` to handle both approve and reject actions**

```python
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries from inline buttons.
    """
    query = update.callback_query
    data = query.data
    
    import asyncio
    
    if data.startswith("approve|"):
        # 1. Answer immediately to stop spinner
        await query.answer(text="🚀 Production started!", show_alert=False)
        
        video_id = data.split("|")[1]
        
        # 2. Update message to confirm approval
        await query.edit_message_text(
            text=f"✅ *Approved:* Starting Production for `{video_id}`..."
        )
        
        # 3. Offload blocking task to a thread
        from src.orchestrator import process_short_approval
        try:
            # Run in thread to keep bot responsive
            await asyncio.to_thread(process_short_approval, video_id, f"Video_{video_id}")
        except Exception as e:
            import logging
            logging.error(f"Error during production for {video_id}: {e}")
            await query.edit_message_text(text=f"❌ *Production Error:* {str(e)}")
            
    elif data.startswith("reject|"):
        # 1. Answer immediately
        await query.answer(text="❌ Recommendation Discarded.", show_alert=False)
        
        # 2. Update message to confirm rejection
        await query.edit_message_text(text="🗑️ *Recommendation Discarded.*")
```

- [ ] **Step 2: Verify syntax and imports**
Ensure `asyncio` is available or imported at the top.

- [ ] **Step 3: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: implement async feedback and rejection handling in telegram bot"
```
