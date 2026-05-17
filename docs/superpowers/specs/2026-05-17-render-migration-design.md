# Design Doc: YouTube Automation Migration to Render.com

**Status:** Draft
**Topic:** Infrastructure Migration (Railway -> Render.com)
**Date:** 2026-05-17

## 1. Overview
This document outlines the architectural transition of the YouTube Shorts Automation system from a local/Railway environment to **Render.com**. The goal is to achieve "Zero Maintenance" with high reliability, persistent state for seen videos, and automated deployments from GitHub.

## 2. Target Architecture

### 2.1 Component Mapping
| Local Component | Render.com Equivalent | Type |
| :--- | :--- | :--- |
| `main.py` (Loop) | **Background Worker** | Persistent Process |
| `seen_videos.json` | **Persistent Disk** | SSD Storage mounted at `/data` |
| `.env` | **Secret Group** | Environment Variables |
| Manual Run | **GitHub Integration** | Continuous Deployment |

### 2.2 Data Flow
1. **Source Control:** Push to GitHub triggers a build on Render.
2. **Environment:** Render injects API keys (Gemini, Telegram, Inworld) via Secret Groups.
3. **Execution:** Render starts a single instance of `python main.py`.
4. **Persistence:** The worker reads/writes to `/data/seen_videos.json`. This disk survives redeploys and restarts.
5. **Logs:** Render captures `stdout/stderr` and provides a real-time log stream.

## 3. Configuration (The `render.yaml` Blueprint)
We will use Render "Blueprints" to define the infrastructure as code.

```yaml
services:
  - type: worker
    name: youtube-automation-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - fromGroup: youtube-automation-secrets
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: SEEN_VIDEOS_PATH
        value: /data/seen_videos.json
    disk:
      name: seen-videos-storage
      mountPath: /data
      sizeGB: 1
```

## 4. Migration Steps (The Roadmap)

### Phase 1: Code Adaptation
- **Path Abstraction:** Modify `config.py` to use an environment variable (`SEEN_VIDEOS_PATH`) for the JSON file location, defaulting to the local path if not set.
- **Port Handling:** Ensure the Telegram bot doesn't try to bind to a port (it already runs in polling mode, which is fine for a Worker).

### Phase 2: Render Setup
- Create a **Secret Group** in Render for Gemini, Telegram, and Inworld keys.
- Create a **Persistent Disk** (1GB is plenty for a JSON file).
- Connect the GitHub Repository.

### Phase 3: Deployment & Validation
- Deploy the Blueprint.
- Monitor logs for initial discovery.
- Test the "Approval" flow via Telegram to ensure the persistent write works.

## 5. Success Criteria
- [ ] Automation starts successfully on Render.
- [ ] `seen_videos.json` persists after a manual service restart.
- [ ] Telegram bot responds to button clicks from the Render environment.
- [ ] New deployments happen automatically upon pushing to the `main` branch.

---

**Self-Review:**
- **Ambiguity:** None. Paths are explicit.
- **Scope:** Focused purely on migration.
- **Consistency:** Matches the "Zero Maintenance" goal.
- **Placeholders:** None.
