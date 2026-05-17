# Refined YouTube Automation Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Telegram interaction to use Approve/Reject buttons, provide immediate feedback, and optimize production to only generate Viral version MP3s with specific scaling rules.

**Architecture:** 
- Update `Systemprompt.md` to redefine word count scaling for 30-40s and 110s targets.
- Modify `telegram_bot.py` to handle dual buttons and immediate "Done" responses.
- Update `orchestrator.py` to skip TTS for the standard version and ensure the Viral MP3 is delivered.

**Tech Stack:** Python, Telegram Bot API, Gemini 3 ProAPI, Inworld AI.

---

### Task 1: Update Reframing Scaling (Gemini System Prompt)

**Files:**
- Modify: `docs/superpowers/specs/Systemprompt.md`

- [ ] **Step 1: Update Layer 2C Scaling Table**

Update the table to match the new duration targets.
- 65-110 words -> 30-40 seconds (75-100 words body)
- 245-300+ words -> 110 seconds (250-300 words body)

```markdown
| Transcript Word Count | Implied Video Duration | Hook (both versions) | Body Word Target | CTA (both versions) |
|-----------------------|------------------------|----------------------|------------------|----------------------|
| 65 – 130 words        | ~30 – 40 seconds       | 10 – 18 words        | 75 – 100 words   | 10 – 18 words        |
| 130 – 200 words       | ~45 – 75 seconds       | 10 – 18 words        | 100 – 175 words  | 10 – 18 words        |
| 200 – 300 words       | ~75 – 110 seconds      | 10 – 18 words        | 175 – 250 words  | 10 – 18 words        |
| 300+ words            | ~110 seconds           | 10 – 18 words        | 250 – 300 words  | 10 – 18 words        |
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/Systemprompt.md
git commit -m "feat: update gemini scaling targets for 30-40s and 110s"
```

---

### Task 2: Implement Approve/Reject Buttons in Telegram Bot

**Files:**
- Modify: `src/telegram_bot.py`

- [ ] **Step 1: Update `send_approval_request` to use dual buttons**

```python
def send_approval_request(video):
    # ... existing config checks ...
    video_id = video.get('yt_videoid')
    title = video.get('title')
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve|{video_id}"},
            {"text": "❌ Reject", "callback_data": f"reject|{video_id}"}
        ]]
    }
    # ... existing payload and request logic ...
```

- [ ] **Step 2: Update `handle_callback` for immediate feedback and dual logic**

```python
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("approve|"):
        await query.answer(text="🚀 Done! Production started.", show_alert=False)
        video_id = data.split("|")[1]
        await query.edit_message_text(text=f"✅ *Approved:* Starting Production for `{video_id}`...")
        
        from src.orchestrator import process_short_approval
        try:
            process_short_approval(video_id, f"Video_{video_id}")
        except Exception as e:
            await query.edit_message_text(text=f"❌ *Error:* {str(e)}")
            
    elif data.startswith("reject|"):
        await query.answer(text="❌ Recommendation Discarded.", show_alert=False)
        await query.edit_message_text(text="🗑️ *Recommendation Discarded.*")
```

- [ ] **Step 3: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: implement approve/reject buttons and immediate feedback"
```

---

### Task 3: Optimize Orchestrator for Viral-Only MP3

**Files:**
- Modify: `src/orchestrator.py`

- [ ] **Step 1: Update `process_short_approval` to skip standard TTS**

```python
def process_short_approval(video_id, title):
    # ... 1. Fetch transcript ...
    # ... 2. Reframe via Gemini ...
    # ... 3. Create directory structure ...

    # 4. Generate audio ONLY for viral version
    v_data = reframed_data.get("viral_version")
    if v_data:
        full_text = f"{v_data['hook']} {v_data['body']} {v_data['cta']}"
        audio_file = os.path.join(output_path, "audio_viral_version.mp3")
        print(f"Generating TTS for viral_version via Inworld...")
        try:
            generate_tts(full_text, audio_file)
        except Exception as e:
            print(f"TTS Error for viral_version: {e}")

    # 5. Notify and send files
    from src.telegram_bot import send_message, send_file, send_audio
    send_message(f"✅ Production completed for: {title}\nViral MP3 and Scripts generated.")
    
    scripts_file = os.path.join(output_path, "scripts.json")
    send_file(scripts_file, caption=f"Scripts for {title}")
    
    audio_file = os.path.join(output_path, "audio_viral_version.mp3")
    if os.path.exists(audio_file):
        send_audio(audio_file, caption=f"Viral Version - {title}", title=f"Viral - {video_id}")
    else:
        send_message(f"❌ Error: Viral MP3 was not generated for {title}")
```

- [ ] **Step 2: Commit**

```bash
git add src/orchestrator.py
git commit -m "perf: optimize production to generate only viral MP3"
```

---

### Task 4: Final Verification

- [ ] **Step 1: Run the bot and test the workflow**
- [ ] **Step 2: Verify only one MP3 is received (Viral)**
- [ ] **Step 3: Verify the length of the scripts in `scripts.json` matches the new scaling**
