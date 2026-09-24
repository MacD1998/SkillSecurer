# OpenClaw Maintenance — Setup Prompts

## With ClawHub (recommended)

```
Install the `hypercho-openclaw-maintenance` skill from ClawHub and set up nightly maintenance.

1. Run: clawhub install hypercho-openclaw-maintenance
2. Dry-run the session cleanup first to preview: python3 <skill_path>/scripts/session_cleanup.py --dry-run
3. If it looks safe, run both scripts for real:
   - python3 <skill_path>/scripts/memory_organize.py
   - python3 <skill_path>/scripts/session_cleanup.py
4. Set up a single midnight cron (0 0 * * *) that runs both scripts daily. Use a cheap model, low thinking, 600s timeout, delivery none.
```

---

## Without ClawHub — Full Self-Contained Prompt

Copy-paste this into any OpenClaw chat. The agent will write both scripts, test them, and set up the cron — no skill install needed.

```
Set up nightly OpenClaw maintenance with two scripts. Write them, test them, and create a midnight cron.

### Script 1: Memory Organizer
Write to: ~/.openclaw/workspace/scripts/memory_organize.py

Purpose: Sort loose .md files from ~/.openclaw/workspace/memory/ root into topic subfolders.

Rules:
- Scan only .md files in the memory/ root (not already in subfolders)
- Route files to subfolders based on keyword matching in filename + content:
  - cabinet/ — keywords: agent, cron, delegation, cabinet, aegis, atlas, echo, clio, argus, vera, quill
  - content/ — keywords: post, blog, marketing, seo, newsletter, clip, postiz
  - products/ — keywords: copanion, hypercho, feature, ui, ux, product, roadmap, release
  - technical/ — keywords: bug, error, config, docs, openclaw, gateway, build, ci, json
  - x/ — keywords: twitter, x.com, viral, engagement, impressions, followers
  - user/ — keywords: ziwen, founder, personal, preference
  - daily/ — fallback for everything else
- Create topic dirs if they don't exist
- Add YAML frontmatter (topic, date, tags) if the file doesn't already have it
- Update an INDEX.md table in each topic folder with the new file entry
- Skip files named INDEX.md
- Make it idempotent — safe to run repeatedly
- No LLM calls — pure keyword matching
- Exit code 2 if nothing to do

### Script 2: Session Cleanup
Write to: ~/.openclaw/workspace/scripts/session_cleanup.py

Purpose: Clean session storage across ALL agents.

Rules:
- Discover all agents by scanning ~/.openclaw/agents/*/sessions/
- For each agent's sessions/ folder:
  1. Delete all tombstone files matching *.reset.*, *.deleted.*, *.bak-*
  2. Load sessions.json. For entries where the key contains "cron" and updatedAt is older than 7 days: delete the corresponding .jsonl file and remove the entry
  3. Delete orphan .jsonl files on disk that aren't referenced by any sessionId in sessions.json
  4. Remove sessions.json entries where key contains "cron" but the .jsonl file doesn't exist
  5. Back up sessions.json to sessions.json.bak before writing changes
- NEVER touch: .lock files, their corresponding .jsonl, main session entries (keys ending in ":main" or equal to "agent:main"), non-cron sessions under 30 days old
- Support --dry-run (preview only) and --agent <name> (single agent)
- Print per-agent summary and total space freed

### After writing both scripts:
1. Run session cleanup with --dry-run and show me the preview
2. If it looks good, run both for real
3. Create a single daily midnight cron (0 0 * * *) that runs both scripts. Use a cheap/fast model, low thinking, 600s timeout, delivery none. The cron message should just run both commands and return stdout.
```
