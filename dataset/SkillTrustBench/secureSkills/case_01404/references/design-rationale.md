# Decision Rationale: Memory System v4

## Evolution Timeline

### 2026-04-04 — Session Start
- Baseline: 329-line AGENTS.md, 23KB MEMORY.md, 10 semantic files (many duplicates)
- System: OpenClaw 2026.4.2, Ubuntu 24.04, Qwen 3.6 Plus via OpenRouter

### Round 1: System Self-Audit
- Cut AGENTS.md 329→111 lines (-66%)
- Cut MEMORY.md 23KB→2.2KB (-90%)
- Removed stale files: ontology, tasks, monitoring, glossary
- Added: tiered loading (HOT/WARM/COLD), 3 memory types, grep tags, weekly review cron
- Added: episodic TTL, buffer rotation, freshness table, open questions

### Round 2: Second AI Consultation
AI feedback: "Structure near saturation — protect against 3 problems: duplicates, partial writes, stale knowledge."

Applied:
- **Atomic write script** (tmp → sync → mv)
- **Canonical Owner Rule** table (one home per fact type)
- **last_verified** in all WARM files
- **Frozen tag vocabulary** (no new tags)
- **Closure blocks** in episodic (Updated/Decisions/Open)

Removed: freshness from episodic (date already in filename), weekly digest conditional

### Round 3: DeepSeek Third Consultation
DeepSeek suggested: Signal Detection, Decision Registry, Friction Log, Boundaries

Applied:
- ✅ **Decision Registry** → `semantic/decisions.md` (8 decisions from audit)
- ✅ **Signal** added to closure blocks (Decision ≠ Signal)
- ✅ **Friction Log** added to working-buffer habit
- ❌ **Boundaries** not created (already in AGENTS.md safety rules)

### Round 4: Consolidation
- Final: 11 files, ~12KB, 10 mechanisms
- Frozen tag vocabulary codified
- All scripts tested
- Ready for ClawHub publication

## What We Rejected and Why

| Rejected | Reason |
|----------|--------|
| Separate decision DB | Already in MEMORY.md + decisions.md |
| Embedding/search layer | Overkill for single-user, grep works fine |
| Frontmatter schema | Adds ceremony without value |
| New memory "types" | 3 types at saturation, more = noise |
| Boundaries file | Already covered in AGENTS.md |
| Per-file intelligence scoring | Maintenance cost > query benefit |
| Separate open-questions file | Already a section in MEMORY.md |

## Key Design Principles

1. **Minimal ceremony** — grep, head, cat. No API, no library chain.
2. **Survive restarts** — everything on disk, nothing in "memory".
3. **Self-healing** — TTL archival, compaction recovery, buffer rotation.
4. **No duplicates** — Canonical Owner Rule enforced by weekly review.
5. **Small context** — 60-line HOT file fits in any prompt budget.
