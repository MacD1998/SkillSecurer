---
name: session-cleanup
description: Clean up OpenClaw session storage across all agents. Removes tombstone files (.reset, .deleted, .bak), old cron session .jsonl files, orphan files, and stale sessions.json entries. Use when session folders are bloated, disk space is low, or as part of daily/nightly maintenance. Triggers on "clean sessions", "session cleanup", "session bloat", "free disk space", "maintenance", "clean up agents".
---

# Session Cleanup

Automated cleanup of OpenClaw session storage across all registered agents.

## What It Cleans

1. **Tombstone files** — `.reset.*`, `.deleted.*`, `.bak-*` (always safe to remove)
2. **Old cron sessions** — `.jsonl` files + `sessions.json` entries older than 7 days for cron-type sessions
3. **Orphan files** — `.jsonl` files on disk not referenced by `sessions.json`
4. **Stale entries** — `sessions.json` entries pointing to missing `.jsonl` files (cron sessions only)

## Safety Guarantees

- Never touches `.lock` files or their corresponding active `.jsonl`
- Never deletes `sessions.json` itself
- Backs up `sessions.json` before modifying
- Never removes non-cron sessions under 30 days old
- Never removes main session entries

## Usage

### Run cleanup for all agents

```bash
python3 <skill_dir>/scripts/session_cleanup.py
```

### Dry run (preview only)

```bash
python3 <skill_dir>/scripts/session_cleanup.py --dry-run
```

### Single agent only

```bash
python3 <skill_dir>/scripts/session_cleanup.py --agent main
```

## Agent Discovery

The script automatically discovers all agents by scanning `~/.openclaw/agents/*/sessions/`. No hardcoded agent list needed — new agents are picked up automatically.

## Cron Integration

Set up as a daily midnight cron job for automatic maintenance:

```
Schedule: 0 0 * * * (midnight local time)
Model: minimax/MiniMax-M2.7-highspeed
Thinking: low
Timeout: 600s
```

Cron task message:

```
Single task only: run session cleanup for all agents.

Command:
bash -lc 'python3 <skill_dir>/scripts/session_cleanup.py'

Return ONLY the command stdout (no extra commentary).
```

## Output Format

The script prints a summary per agent showing what was cleaned, then a grand total:

```
Agents discovered: 22

  ada: 165 tombstones (21.1 MB), 7 old crons (372 KB)
  vera: 924 tombstones (31.6 MB), 4 old crons (252 KB)

✅ Session cleanup complete across 22 agents
   Freed: 171.6 MB
   Cleaned: ada, vera
   Already clean: main, clio, argus
```

If nothing needs cleaning, it reports "Already clean. Nothing to do."

## Retention Policy

| Session Type | Retention | Action |
|-------------|-----------|--------|
| Tombstones (.reset/.deleted/.bak) | 0 days | Always delete |
| Cron session files | 7 days | Delete after 7 days |
| Non-cron sessions | 30 days | Keep (no auto-delete) |
| Main sessions | Forever | Never touched |
| Active sessions (.lock) | Forever | Never touched |
