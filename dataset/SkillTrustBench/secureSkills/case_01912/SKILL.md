---
name: openclaw-maintenance
description: Nightly maintenance for OpenClaw — memory organization (sort loose memory files into topic folders with frontmatter and INDEX.md) and session cleanup (purge tombstones, old cron sessions, orphans across all agents). Use when memory files are disorganized, session folders are bloated, disk space is low, or to set up automated daily maintenance. Triggers on "clean sessions", "organize memory", "maintenance", "session bloat", "memory cleanup", "free disk space", "nightly cleanup".
---

# OpenClaw Maintenance

Two scripts that keep your OpenClaw instance lean: memory organization and session cleanup.

## 1. Memory Organizer

Sorts loose `.md` files from `~/.openclaw/workspace/memory/` root into topic subfolders.

### What it does

- Scans `memory/*.md` for files sitting in the root (not already in a subfolder)
- Routes each file to a topic folder based on keyword matching:
  - `cabinet/` — agent, cron, delegation, cabinet agent names
  - `content/` — post, blog, marketing, seo, clips
  - `products/` — copanion, hypercho, feature, ui, roadmap
  - `technical/` — bug, error, config, docs, gateway
  - `x/` — twitter, viral, engagement, followers
  - `user/` — ziwen, founder, personal
  - `daily/` — fallback for everything else
- Adds YAML frontmatter (topic, date, tags) if missing
- Updates `INDEX.md` in each topic folder with the new file
- Idempotent — safe to run repeatedly
- No LLM dependency — pure keyword matching

### Run

```bash
python3 <skill_dir>/scripts/memory_organize.py
```

## 2. Session Cleanup

Cleans session storage across ALL registered agents.

### What it cleans

| Target | Retention | Action |
|--------|-----------|--------|
| Tombstones (`.reset.*`, `.deleted.*`, `.bak-*`) | 0 days | Always delete |
| Cron session `.jsonl` files | 7 days | Delete after 7 days |
| Orphan `.jsonl` (on disk, not in sessions.json) | 0 days | Delete |
| Stale sessions.json entries (cron, file missing) | 0 days | Remove entry |
| Non-cron sessions | 30 days | Keep |
| Main sessions | Forever | Never touched |
| Active sessions (`.lock`) | Forever | Never touched |

### Safety

- Auto-discovers agents by scanning `~/.openclaw/agents/*/sessions/`
- Backs up `sessions.json` before modifying
- Never touches locked/active sessions

### Run

```bash
# All agents
python3 <skill_dir>/scripts/session_cleanup.py

# Preview only
python3 <skill_dir>/scripts/session_cleanup.py --dry-run

# Single agent
python3 <skill_dir>/scripts/session_cleanup.py --agent main
```

## Cron Setup

Set up a single midnight cron that runs both scripts:

```
Schedule: 0 0 * * * (midnight local time)
Model: any cheap/fast model
Thinking: low
Timeout: 600s
Delivery: none
```

Cron task message:

```
Single task only: run memory organizer and session cleanup.

Command 1 (memory):
bash -lc 'python3 <skill_dir>/scripts/memory_organize.py'

Command 2 (sessions):
bash -lc 'python3 <skill_dir>/scripts/session_cleanup.py'

Return ONLY the combined stdout (no extra commentary).
```
