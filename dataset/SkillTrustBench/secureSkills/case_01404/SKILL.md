---
name: openclaw-memory-canonical
description: >
  Lightweight file-based memory system for single-user AI agents. Uses markdown files only: HOT/WARM/COLD/BUFFER plus SCRATCH learnings,
  with tiered loading, WAL-lite writes, compaction recovery, weekly review, TTL archival, health checks, and a built-in self-improvement loop.
  Use when setting up or improving agent memory, preventing memory bloat or repeated mistakes, promoting recurring lessons into durable files,
  validating memory health, or when users mention memory systems, working buffers, episodic/semantic/procedural memory, learnings, weekly review,
  self-improvement, or how an AI agent should remember and improve between sessions.
---

# OpenClaw Memory v4.5.4 (2026-04-07)

File-based memory system for single-user AI agents: HOT/WARM/COLD/BUFFER + SCRATCH. ~12KB, 9 files, zero dependencies.

## Execution

### Runtime Decision Tree (for AI execution)

**On session start:**
1. Read `MEMORY.md`. Output: HOT context loaded.
2. Read `memory/working-buffer.md`. Output: current task state loaded.
3. If `memory/working-buffer.md.pending` exists, recover `memory/working-buffer.md.pending` before any review or maintenance. Output: pending rotation data recovered or explicit decision that no pending recovery is needed.
4. If `memory/working-buffer.md` is stale (>2h) and unfinished, recover pending work first. Output: either recovered task state or explicit decision that no recovery is needed.
5. Read episodic notes for today and yesterday. Output: recent events and decisions loaded.
6. Scan the last 20 lines of `.learnings/ERRORS.md`, `.learnings/LEARNINGS.md`, and `.learnings/FEATURE_REQUESTS.md` if those files exist. Output: matching lessons loaded or no-op if nothing relevant exists.
7. Resume from file contents. Stop when the active task or current request has enough memory context to continue safely.

**Before major memory work:**
1. Re-scan `.learnings/*` only if the task changed materially or a prior attempt already failed. Output: refreshed lesson candidates or no-op.
2. If a prior lesson clearly matches the current task, apply it. Output: adjusted plan or command.
3. If nothing matches, continue silently. Stop after either applying one relevant lesson or confirming that nothing relevant matched.

**Before writing any important fact:**
- Write the fact to `memory/working-buffer.md` first.
- Then reply or continue the task.

**After a failure, correction, or missing capability:**
- Log one concise line in the matching `.learnings/` file.
- If the lesson is broadly reusable, promote it to the right durable file.
- Do not log `nothing found` or other no-op activity.

**When `working-buffer.md` grows too large:**
- If the current task is complex and still active, defer rotation until session end.
- Otherwise rotate the buffer into episodic notes and create a fresh buffer.

**If `health-check.sh` fails:**
- Stop memory-dependent reasoning.
- Tell the user: `Memory integrity check failed. Run bash memory/scripts/health-check.sh`.
- You may still greet, clarify the current request, explain what memory is broken, or help fix the failing check.
- Do not answer questions that require retrieving semantic memory, procedural memory, or older episodic facts until the check is fixed.

**When searching memory:**
- HOT → `MEMORY.md` is always in context.
- WARM → search `memory/semantic/` and `memory/procedural/` first.
- COLD → search `memory/episodic/` only when needed.

**Never:**
- Write the same fact to two different files.
- Delete memory files directly when archival or trash is the safer path.
- Store credentials in episodic notes.
- Invent new tags outside the frozen vocabulary.
- Duplicate the same lesson across multiple `.learnings/` files.

## Core Design

3 types, 4 primary tiers + SCRATCH, 10 mechanisms that fit in a terminal.

### 3 Types

| Type | What | Lives |
|------|------|-------|
| **Episodic** | What happened | `memory/episodic/YYYY-MM-DD.md` |
| **Semantic** | What I know | `memory/semantic/*.md` |
| **Procedural** | How to do things | `memory/procedural/*.md` |

### 4 Primary Tiers + SCRATCH

| Tier | Files | When to load |
|------|-------|-------------|
| **HOT** | `MEMORY.md` (≤60 lines) | Every session |
| **WARM** | `semantic/*.md`, `procedural/*.md` | By context (grep tags) |
| **COLD** | `episodic/`, `archive/` | On query |
| **BUFFER** | `working-buffer.md` | During active task |
| **SCRATCH** | `.learnings/*.md` | Session start (scan recent relevant lines) |

### Directory Structure

```
MEMORY.md                          ← HOT, ≤60 lines, always loaded
├── .learnings/                    ← SCRATCH, recent failures/corrections/capability gaps
│   ├── ERRORS.md
│   ├── LEARNINGS.md
│   └── FEATURE_REQUESTS.md
├── memory/
│   ├── episodic/                  ← COLD, one per day
│   │   └── YYYY-MM-DD.md          ← events, decisions, signals
│   ├── semantic/                  ← WARM, one per domain
│   │   ├── infrastructure.md      ← IP, ports, services
│   │   ├── preferences.md         ← style, rules, habits
│   │   ├── projects.md            ← active projects
│   │   └── decisions.md           ← final decisions with why
│   ├── procedural/                ← WARM, how-to + lessons
│   │   ├── lessons-learned.md     ← post-mortems, anti-patterns
│   │   └── (other how-to files)
│   ├── working-buffer.md          ← BUFFER, active task scratchpad
│   ├── archive/YYYY/MM/           ← episodic >30 days, auto-moved
│   ├── archive/learnings/YYYY/MM/ ← SCRATCH entries >30 days without promotion
│   └── scripts/
│       ├── archive-old-episodic.sh ← TTL archiver
│       ├── atomic-write.sh         ← crash-safe file writes
│       └── health-check.sh         ← invariant validation
```

## 11 Mechanisms

**Execution precedence for weak models:**
- If the same task appears in two sections, follow the earlier runtime branch that names the exact condition.
- If a summary section and a detailed section disagree, follow the detailed section and patch the summary on the next maintenance pass.
- The canonical startup read order is: `MEMORY.md` → `memory/working-buffer.md` → today's and yesterday's episodic notes → recent relevant `.learnings/*` lines.

### 1. Buffer-first writes

Before answering with important info (decisions, corrections, facts), write to `working-buffer.md` first. Then reply. Files survive restarts.

**Working buffer header format (v4.1+):**
```markdown
# Working Buffer
created: 2026-04-05T14:31:00+08:00
last_active: 2026-04-05T14:31:00+08:00

## Active Task:
- ...
```

Header enables:
- **Stale detection:** If `last_active` > 2 hours and no current session working on it → abandoned buffer
- **Compaction recovery:** Distinguish current task from leftover buffer

### 2. Startup Read Sequence

After session compaction or reset:
1. Read `MEMORY.md`.
2. Read `memory/working-buffer.md`.
3. If `memory/working-buffer.md` is stale and unfinished, recover pending work first.
4. Read episodic notes for today and yesterday.
5. Scan recent relevant lines in `.learnings/ERRORS.md`, `.learnings/LEARNINGS.md`, and `.learnings/FEATURE_REQUESTS.md` if those files exist.
6. Resume from file contents.

### 3. Canonical Owner Rule — Principle, Not Mechanism

This is a design rule, not a runtime branch table. Use it to decide where a fact belongs. Do not treat it as a step-by-step workflow.

Each class of fact has exactly one home. Never duplicate:

| Fact type | Lives in |
|-----------|----------|
| IP, ports, services | `semantic/infrastructure.md` |
| Preferences, style, rules | `semantic/preferences.md` |
| Commands, how-to | `procedural/*.md` |
| Events, decisions, timeline | `episodic/YYYY-MM-DD.md` |
| Post-mortems, anti-patterns | `procedural/lessons-learned.md` |
| Final decisions with rationale | `semantic/decisions.md` |

### 4. Atomic Writes

Prevent corrupted files on crash. Prefer the bundled script:

```bash
echo "content" | bash scripts/atomic-write.sh /path/to/file.md
```

Manual fallback if the script is unavailable:

```bash
TMP=$(mktemp /path/to/file.md.tmp.XXXX)
echo "content" > "$TMP"
cp --force "$TMP" /path/to/file.md && sync
rm -f "$TMP"
```

Rule: write the complete temp file first. Replace the target file only after the temp file is complete.

### 5. Closure Blocks in Episodic

End every episodic note with 4 lines:

```
Updated: YYYY-MM-DD
Decisions: what was changed
Signal: what I learned about the system
Open: remaining items (or "none")
```

Decision = what I changed. Signal = what I learned.

### 6. Episodic TTL

Archive files older than N days into `archive/YYYY/MM/`:

```bash
bash scripts/archive-old-episodic.sh 30   # default 30
```

### 6b. SCRATCH TTL (`.learnings/`)

Files in `.learnings/` expire after 30 days without promotion:
- last-modified >30 days → move to `memory/archive/learnings/YYYY/MM/`
- never delete permanently (`trash` > `rm`)
- entries tagged `#pinned:` are exempt until manually unpinned
- keep the active SCRATCH surface canonical: `ERRORS.md`, `LEARNINGS.md`, `FEATURE_REQUESTS.md`
- move legacy scratch notes into `memory/archive/learnings/YYYY/MM/` rather than leaving mixed formats active

### 7. Buffer Rotation

When `working-buffer.md` exceeds 80 lines:
1. Create `working-buffer.md.lock` before rotation starts.
2. Atomically move buffer: `mv working-buffer.md "working-buffer.md.rotating"`
3. Append rotated content: `cat "working-buffer.md.rotating" >> episodic/$(date +%Y-%m-%d).md`
4. On success: `rm -f "working-buffer.md.rotating"`
5. On failure: `mv "working-buffer.md.rotating" "working-buffer.md.pending"` (preserves data)
6. Touch new working-buffer.md with timestamp header
7. Remove `working-buffer.md.lock` after rotation completes, whether rotation succeeded or failed
8. Continue

**Recovery:** If `working-buffer.md.pending` exists, recover it before any further review or maintenance. If `working-buffer.md.lock` exists, remove it only after confirming no active rotation is running.

**Operational rule from real use:** weekly review must not continue past health-check when the buffer is oversized. First restore a healthy buffer, then run weekly review.

Rotation is soft — if in the middle of a complex task, defer until session end.

### 8. Weekly Review (cron, Monday 9:00)

**Minimal safe v1 weekly review** should automate only deterministic maintenance plus candidate detection.

**Session detection for weekly review:**
- if `working-buffer.md.lock` exists, treat the session as active
- if `working-buffer.md` has `last_active` less than 2 hours ago, treat the session as active
- if only `.lock` exists but `last_active` is older than 2 hours, treat the lock as stale, log a warning, and continue only after confirming no rotation process is running
- if either non-stale signal says active, skip/defer review, log that decision, and stop the current review run

Automated review that:
1. Checks for an active session; if a live session is active, skip/defer review
2. Runs `health-check.sh`; if it FAILs, stop review and fix health first
3. Runs episodic archival (>30 days)
4. Runs `.learnings/` archival (>30 days without promotion)
5. Scans `.learnings/ERRORS.md` and `.learnings/LEARNINGS.md` for repeated lessons and flags 3+ occurrence patterns as promotion candidates for manual review
6. Warns if `working-buffer.md` is oversized, but does not auto-rotate during review
7. Appends a closure-compatible maintenance note to today's episodic file

Do **not** do these automatically in v1:
- semantic extraction from episodic notes beyond counting repeated lesson patterns
- lesson promotion into semantic/procedural memory
- `last_verified` refresh
- `MEMORY.md` rewrite
- forced working-buffer rotation during review

If nothing meaningful changed → skip with "No meaningful changes".

### 9. Health Check (invariant validation)

Before important operations, run:

```bash
bash scripts/health-check.sh
```

Health check should cover at least: tags on line 2, frozen vocabulary, last_verified <30d, buffer <80 lines, open questions ≤5, closure blocks, Active Decisions link integrity, episodic file count, WAL integrity (no orphaned buffer entries), and active-session conflict handling for weekly maintenance.
Returns exit code 0 if all pass, 1 if any fail.

Treat `health-check.sh` as a separate script in the reference implementation, not as implicit model behavior.

**Health check failures — quick fixes:**
- `tags on line 2 missing` → add `#tags: <frozen-vocabulary>` as line 2
- `last_verified >30d` → update `last_verified: YYYY-MM-DD` in the file header after real verification
- `buffer >80 lines` → rotate or recover the working buffer before running weekly review
- `closure blocks missing` → add the 4-line closure block to the episodic file
- `active session detected` → defer weekly review rather than writing concurrently
- any other FAIL → run `bash scripts/health-check.sh --verbose` and fix the reported invariant

### 10. Grep-Based Tag Discovery

Every WARM file has `#tags:` on line 2:

```bash
grep -rl "qdrant" memory/                         # all files mentioning qdrant
grep -rl "#tags:.*networking" memory/              # files tagged networking
head -2 memory/**/*.md | grep "#tags:"             # discover all tags
```

### 11. Self-Improvement Loop

Capture only lessons that should change future behavior.

**Write immediately after:**
- a command fails
- a user corrects the agent
- a capability is missing
- an external tool or API fails
- knowledge is outdated
- a better recurring approach is discovered

**Use these files:**
- `.learnings/ERRORS.md` → what failed, why, and the fix attempt
- `.learnings/LEARNINGS.md` → what was wrong and the better way
- `.learnings/FEATURE_REQUESTS.md` → the missing capability, impact, and desired behavior

**Promotion to durable memory:**

Promote from `.learnings/` to a durable file only when one of these is true:
1. The user explicitly says `remember this`, `make this permanent`, or equivalent.
2. The lesson prevents data loss, a security issue, or an unrecoverable error.
3. Manual review explicitly approves promotion after a recurring pattern is observed.

If the same lesson appears 3 or more times in the past 7 days, treat it as a promotion candidate for manual review. Do not auto-promote it only because it repeated.

Otherwise keep it in `.learnings/`.

**Target mapping for promotion:**
- command syntax, debugging steps, repeatable fixes →
  - if the lesson fits an existing procedural file, append there
  - otherwise create `memory/procedural/<topic>.md` only after 3 or more promotions on the same topic
- infrastructure facts, preferences, durable facts → `memory/semantic/*.md`
- anti-patterns and post-mortems → `memory/procedural/lessons-learned.md` (always, not generic procedural)
- decisions with rationale → `memory/semantic/decisions.md`

**Do not promote:**
- one-off fixes
- session-specific context
- preferences that matter only for today

**Anti-patterns:**
- Do not log `checked learnings, nothing relevant`.
- Do not duplicate the same lesson across `ERRORS.md` and `LEARNINGS.md`.
- Do not write more than two short sentences per entry unless the case is genuinely complex.
- If scan finds nothing relevant to the current task, do nothing.

## Tag Vocabulary (Frozen)

**infrastructure:** tailscale, tailnet, docker, synapse, matrix, coturn, qdrant, ubuntu, systemd, ufw, fail2ban, samba, ssh, networking, gateway, pm2
**preferences:** rules, style, workflow, memory, habits
**projects:** audit, skills, security, review
**procedural:** deepseek, puppeteer, benchmark, troubleshooting, tasks, checklist, backup, diagnostics
**lessons:** postmortem, errors, fixes, anti-patterns

Do not invent new tags.

## Friction Log

If a task takes >5 minutes of waiting/googling → note it inline with `#friction:` tag in the working buffer. Weekly review may record that friction exists, but in the minimal safe v1 it should not auto-promote friction into `lessons-learned.md` without manual review.

## Known Limits (documented, not fixed)

- **No file locking for concurrent writes** — Single writer assumed; stagger crons to avoid overlap between cron jobs and main session
- **No auto-promotion**: Important signals in old episodic files don't auto-surface to semantic; relies on weekly review to surface candidates, not to promote automatically
- **Tag enforcement is trust-based**: Health-check validates tags against frozen vocabulary, but doesn't prevent writing new tags
- **Weekly review is intentionally minimal**: it performs deterministic maintenance, not semantic judgment

## Safety Rules

- `trash` > `rm` — never delete, always move
- Atomic writes for all file modifications
- No duplicate facts across files (Canonical Owner)
- No duplicate lessons across `.learnings/` files
- No credentials in episodic notes
- Commit changes after updates
- Weekly review validates `last_verified` dates

## Why This Works

- **Text > brain**: Files survive restarts. Mental notes don't.
- **Grep > database**: No vector DB, no API, no dependency chain.
- **Small context**: 60-line MEMORY.md fits in any prompt.
- **Self-maintaining**: TTL archival + weekly review + health check + buffer rotation.
- **Hard to break**: Atomic writes, canonical owners, frozen tags, invariant checks.
- **Reality-tested**: validation drill catches integration failures before they become memory corruption.

See `references/design-rationale.md` for the full decision trail from the 4-round AI consultation that shaped this system.
