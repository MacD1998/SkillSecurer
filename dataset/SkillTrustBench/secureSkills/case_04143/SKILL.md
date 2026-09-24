---
name: context-window-tracker
description: >
  Track and report OpenClaw context window usage with a detailed breakdown of what's
  consuming tokens. Use when: user asks about context usage, token usage,
  "how much context am I using", "how full is my context window", "tokens remaining",
  "am I close to the limit", thinking/reasoning token costs, what's eating context
  (session setup vs conversation vs overhead), or how many turns are left.
  NOT for: estimating tokens for arbitrary text, managing context (compact/prune),
  or cross-session cost aggregation.
homepage: https://github.com/99rebels/context-window-tracker
---

# Context Window Tracker

Shows how much context window is left, without opening the terminal.

## When to Use

- "Check my context"
- "How much context am I using?"
- "How full is my context window?"
- "Tokens remaining"
- "Am I close to the limit?"
- Any question about context usage

## Two Modes

### Compact (default)
One line, glanceable. Good for quick checks.

```bash
python3 scripts/context_report.py
```

### Detailed
Full breakdown with per-file system prompt, conversation split, trends, and thinking status. Use when the user asks for specifics.

```bash
python3 scripts/context_report.py --detailed
```

Both modes auto-detect the most recently updated session. Options:

```
--session <key>    Target a specific session
--agent <name>     Target a specific agent (default: main)
--detailed         Full breakdown instead of compact one-liner
```

## Output Format

### Compact
```
🟢 [███░░░░░░░░░░░░░░░░░] 29.8K / 202.8K tokens (15% used) | ~736 turns left | Cache: 99%
```

### Detailed
```
🟢 [███░░░░░░░░░░░░░░░░░] Context Usage: 29.8K / 202.8K (15%)

────────────────────
**Token Breakdown**
  System Prompt: ~10.2K tokens (5%)
    AGENTS.md: ~2.0K
    SOUL.md: ~416
    TOOLS.md: ~717
    MEMORY.md: ~2.3K
  📦 Framework overhead: ~5.3K (tool schemas, skill list, runtime)
  Conversation: ~19.6K tokens (10%)
  📊 Total Used: 29.8K (15%)
  Remaining: 173.0K (85%)

────────────────────
**Trends**
  Avg tokens per turn: ~1.2K tokens
  ⏳ Estimated turns remaining: ~144

────────────────────
**Session Stats**
  📥 Total input: 25K | 📤 Total output: 1.8K | Cache hit rate: 99%
  Thinking: active (3/12 responses)
────────────────────
```

The bar uses `█` (filled) and `░` (empty) across 20 segments (each = 5%). The indicator shifts: 🟢 under 60%, 🟡 60-80%, 🔴 over 80%.

## Guidance

When the user asks about context usage, you may optionally include a brief note about remaining capacity based on the script output and the current conversation. Only do this at 75%+ usage. Skip for fresh sessions.

Rules:
- One line max. Reference the actual task, not generic categories.
- Don't prescribe actions, describe what fits.
- Never suggest deleting workspace files or changing system config.

## What's Exact vs Estimated

```
✅ Exact (from provider):
  • Total tokens used (from transcript)
  • Context window limit (from session store)
  • Cache hit rate

⚠ Estimated:
  • Per-file system prompt breakdown (chars ÷ 4)
  • Turns remaining (extrapolated from recent growth rate)
  • Thinking token count (bundled by provider, not separately reported)
```

## Notes

- Script reads the transcript (`.jsonl`) as source of truth. The session store can lag behind by thousands of tokens.
- If the context window limit is unknown, the script shows tokens used without a percentage.
- See [references/data-sources.md](references/data-sources.md) for file paths
- See [references/thinking-tokens.md](references/thinking-tokens.md) for how reasoning tokens affect counts
