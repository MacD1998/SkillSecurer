# Session Cleanup — Setup Prompt

Copy-paste this into your OpenClaw chat to install and configure automatic session cleanup.

---

## The Prompt

```
Install the `hypercho-session-cleanup` skill from ClawHub and set up automatic nightly session cleanup for my OpenClaw instance.

Steps:
1. Run `clawhub install hypercho-session-cleanup` to install the skill
2. Do a dry run first: `python3 <skill_path>/scripts/session_cleanup.py --dry-run` — show me how much space will be freed
3. If the dry run looks good, run it for real to clean up now
4. Set up a daily midnight cron job that runs the cleanup script across ALL agents automatically

The script should:
- Scan ~/.openclaw/agents/*/sessions/ to discover all agents
- Delete tombstone files (.reset.*, .deleted.*, .bak-*) — always safe to remove
- Remove cron session .jsonl files older than 7 days
- Clean up orphan .jsonl files not referenced by sessions.json
- Remove stale sessions.json entries pointing to missing files
- Never touch active sessions (with .lock files), main sessions, or non-cron sessions under 30 days old
- Back up sessions.json before modifying it

Cron config:
- Schedule: midnight daily (0 0 * * *)
- Model: use whatever cheap/fast model is available
- Thinking: low
- Timeout: 600s
- Delivery: none (silent maintenance)
```

---

## Minimal Version (if skill is already installed)

```
Run the session-cleanup skill to clean up session storage across all my agents. Do a dry run first, then clean for real. Set up a midnight cron to run it daily.
```
