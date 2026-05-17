# Optimize Orchestrator for Viral-Only MP3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify `process_short_approval` to generate and send only the Viral version MP3, while still saving the JSON for both versions.

**Architecture:** Update the logic in `src/orchestrator.py` to only call `generate_tts` for the `viral_version` and update the Telegram notification to reflect this.

**Tech Stack:** Python, `os`, `json`, `src.telegram_bot`.

---

### Task 1: Modify `process_short_approval` in `src/orchestrator.py`

**Files:**
- Modify: `src/orchestrator.py`

- [ ] **Step 1: Read the current file content**
Ensure we have the latest version of `src/orchestrator.py`.

- [ ] **Step 2: Update TTS generation logic**
Change the loop that generates audio for both versions to only target `viral_version`.

```python
<<<<
    # 4. Generate audio for both versions
    for version in ["viral_version", "standard_version"]:
        v_data = reframed_data.get(version)
        if not v_data:
            continue
            
        full_text = f"{v_data['hook']} {v_data['body']} {v_data['cta']}"
        audio_file = os.path.join(output_path, f"audio_{version}.mp3")
        
        print(f"Generating TTS for {version} via Inworld...")
        try:
            generate_tts(full_text, audio_file)
        except Exception as e:
            print(f"TTS Error for {version}: {e}")
====
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
>>>>
```

- [ ] **Step 3: Update Telegram notification and delivery logic**
Update the message sent to the user and ensure only the viral audio is sent.

```python
<<<<
    # 5. Notify user and send files via Telegram
    from src.telegram_bot import send_message, send_file, send_audio
    
    send_message(f"✅ Production completed for: {title}\nBoth Viral and Standard versions generated.")
    
    # Send the scripts JSON
    scripts_file = os.path.join(output_path, "scripts.json")
    send_file(scripts_file, caption=f"Scripts for {title}")
    
    # Send both audio versions
    for version in ["viral_version", "standard_version"]:
        audio_file = os.path.join(output_path, f"audio_{version}.mp3")
        if os.path.exists(audio_file):
            send_audio(audio_file, caption=f"{version.replace('_', ' ').title()} - {title}", title=f"{version} - {video_id}")
====
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
>>>>
```

- [ ] **Step 4: Verify the changes**
Run a syntax check and manually review the code.

Run: `python -m py_compile src/orchestrator.py`

- [ ] **Step 5: Commit changes**

```bash
git add src/orchestrator.py
git commit -m "perf: optimize production to generate only viral MP3"
```
