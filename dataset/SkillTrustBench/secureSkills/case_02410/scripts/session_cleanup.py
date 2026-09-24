#!/usr/bin/env python3
"""
Session Cleanup Script for OpenClaw (All Agents)
==================================================
Runs daily to keep session folders lean across ALL agents.

What it does per agent:
1. Deletes all tombstone files (.reset.*, .deleted.*, .bak-*)
2. Removes old cron session .jsonl files (>7 days) and their sessions.json entries
3. Removes orphan .jsonl files (on disk but not in sessions.json)
4. Cleans sessions.json entries that reference missing .jsonl files (cron-only)
5. Protects: main session, active sessions (.lock files), non-cron sessions <30 days old

Safety:
- Never touches .lock files or their corresponding .jsonl
- Never deletes sessions.json itself
- Writes a backup of sessions.json before modifying
- Dry-run mode available via --dry-run flag

Usage:
  python3 session_cleanup.py              # Clean all agents
  python3 session_cleanup.py --dry-run    # Preview only
  python3 session_cleanup.py --agent main # Single agent only
"""

import json
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

AGENTS_BASE = Path.home() / ".openclaw" / "agents"
CRON_RETENTION_DAYS = 7
NON_CRON_RETENTION_DAYS = 30
DRY_RUN = "--dry-run" in sys.argv

# Parse --agent flag for single-agent mode
SINGLE_AGENT = None
if "--agent" in sys.argv:
    idx = sys.argv.index("--agent")
    if idx + 1 < len(sys.argv):
        SINGLE_AGENT = sys.argv[idx + 1]


def log(msg):
    print(msg)


def discover_agents():
    """Discover all agents by scanning ~/.openclaw/agents/*/sessions/."""
    agents = []
    if not AGENTS_BASE.exists():
        return agents
    for d in sorted(AGENTS_BASE.iterdir()):
        if d.is_dir() and (d / "sessions").is_dir():
            agents.append(d.name)
    return agents


def is_cron_session(key):
    return "cron" in key


def is_main_session(key):
    return key.endswith(":main") or key == "agent:main"


def get_active_session_ids(sessions_dir):
    """Find session IDs with active .lock files."""
    active = set()
    for f in sessions_dir.glob("*.jsonl.lock"):
        sid = f.name.replace(".jsonl.lock", "")
        active.add(sid)
    return active


def delete_tombstones(sessions_dir):
    """Delete .reset.*, .deleted.*, .bak-* files."""
    deleted_count = 0
    freed_bytes = 0

    patterns = ["*.reset.*", "*.deleted.*", "*.bak-*"]
    for pattern in patterns:
        for f in sessions_dir.glob(pattern):
            size = f.stat().st_size
            if not DRY_RUN:
                f.unlink()
            deleted_count += 1
            freed_bytes += size

    return deleted_count, freed_bytes


def load_sessions_json(sessions_dir):
    """Load sessions.json, return dict."""
    sjson = sessions_dir / "sessions.json"
    if not sjson.exists():
        return {}
    try:
        with open(sjson, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_sessions_json(sessions_dir, data):
    """Save sessions.json with backup."""
    sjson = sessions_dir / "sessions.json"
    if DRY_RUN:
        return

    # Backup
    backup = sjson.with_suffix(".json.bak")
    if sjson.exists():
        shutil.copy2(sjson, backup)

    with open(sjson, "w") as f:
        json.dump(data, f)


def cleanup_cron_sessions(sessions_dir, sessions, active_ids):
    """Remove old cron sessions from sessions.json and disk."""
    cutoff_ms = (time.time() - CRON_RETENTION_DAYS * 86400) * 1000
    removed_keys = []
    deleted_files = 0
    freed_bytes = 0

    for key, meta in list(sessions.items()):
        if not is_cron_session(key):
            continue
        if is_main_session(key):
            continue

        sid = meta.get("sessionId", "")
        if sid in active_ids:
            continue

        updated = meta.get("updatedAt", 0)
        if updated > cutoff_ms:
            continue

        # Old cron session — mark for removal
        removed_keys.append(key)

        # Delete .jsonl file if it exists
        jsonl_file = sessions_dir / f"{sid}.jsonl"
        if jsonl_file.exists():
            size = jsonl_file.stat().st_size
            if not DRY_RUN:
                jsonl_file.unlink()
            deleted_files += 1
            freed_bytes += size

    for key in removed_keys:
        if not DRY_RUN:
            del sessions[key]

    return len(removed_keys), deleted_files, freed_bytes


def cleanup_orphan_files(sessions_dir, sessions, active_ids):
    """Delete .jsonl files on disk not referenced by sessions.json."""
    referenced_ids = set()
    for meta in sessions.values():
        sid = meta.get("sessionId", "")
        if sid:
            referenced_ids.add(sid)

    deleted = 0
    freed_bytes = 0

    for f in sessions_dir.glob("*.jsonl"):
        sid = f.stem
        if sid in referenced_ids:
            continue
        if sid in active_ids:
            continue

        size = f.stat().st_size
        if not DRY_RUN:
            f.unlink()
        deleted += 1
        freed_bytes += size

    return deleted, freed_bytes


def cleanup_stale_entries(sessions_dir, sessions, active_ids):
    """Remove sessions.json entries where the .jsonl file is missing AND it's a cron session."""
    removed = 0
    for key, meta in list(sessions.items()):
        if not is_cron_session(key):
            continue
        sid = meta.get("sessionId", "")
        if not sid:
            continue
        if sid in active_ids:
            continue

        jsonl_file = sessions_dir / f"{sid}.jsonl"
        if not jsonl_file.exists():
            if not DRY_RUN:
                del sessions[key]
            removed += 1

    return removed


def clean_agent(agent_name):
    """Run full cleanup for one agent. Returns (freed_bytes, stats_dict)."""
    sessions_dir = AGENTS_BASE / agent_name / "sessions"
    if not sessions_dir.exists():
        return 0, None

    active_ids = get_active_session_ids(sessions_dir)

    # Step 1: Delete tombstones
    tomb_count, tomb_bytes = delete_tombstones(sessions_dir)

    # Step 2: Load sessions.json
    sessions = load_sessions_json(sessions_dir)
    pre_entries = len(sessions)

    # Step 3: Clean old cron sessions
    cron_removed, cron_files, cron_bytes = cleanup_cron_sessions(sessions_dir, sessions, active_ids)

    # Step 4: Clean orphan files
    orphan_count, orphan_bytes = cleanup_orphan_files(sessions_dir, sessions, active_ids)

    # Step 5: Clean stale entries
    stale_count = cleanup_stale_entries(sessions_dir, sessions, active_ids)

    # Step 6: Save if changed
    post_entries = len(sessions)
    if post_entries != pre_entries:
        save_sessions_json(sessions_dir, sessions)

    total_freed = tomb_bytes + cron_bytes + orphan_bytes
    total_actions = tomb_count + cron_removed + orphan_count + stale_count

    stats = {
        "tombstones": tomb_count,
        "tomb_bytes": tomb_bytes,
        "cron_entries": cron_removed,
        "cron_files": cron_files,
        "cron_bytes": cron_bytes,
        "orphans": orphan_count,
        "orphan_bytes": orphan_bytes,
        "stale": stale_count,
        "entries_before": pre_entries,
        "entries_after": post_entries,
        "total_freed": total_freed,
        "total_actions": total_actions,
    }

    return total_freed, stats


def format_size(b):
    if b >= 1024 * 1024:
        return f"{b / 1024 / 1024:.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.0f} KB"
    return f"{b} B"


def main():
    if DRY_RUN:
        log("=== DRY RUN MODE ===\n")

    # Discover agents
    if SINGLE_AGENT:
        agents = [SINGLE_AGENT]
    else:
        agents = discover_agents()

    if not agents:
        log("No agents found. Nothing to do.")
        return

    log(f"Agents discovered: {len(agents)}")
    log("")

    grand_freed = 0
    grand_actions = 0
    agent_results = []

    for agent in agents:
        freed, stats = clean_agent(agent)
        if stats is None:
            continue

        grand_freed += freed
        grand_actions += stats["total_actions"]

        if stats["total_actions"] > 0:
            parts = []
            if stats["tombstones"] > 0:
                parts.append(f"{stats['tombstones']} tombstones ({format_size(stats['tomb_bytes'])})")
            if stats["cron_entries"] > 0:
                parts.append(f"{stats['cron_entries']} old crons ({format_size(stats['cron_bytes'])})")
            if stats["orphans"] > 0:
                parts.append(f"{stats['orphans']} orphans ({format_size(stats['orphan_bytes'])})")
            if stats["stale"] > 0:
                parts.append(f"{stats['stale']} stale entries")
            if stats["entries_before"] != stats["entries_after"]:
                parts.append(f"sessions.json {stats['entries_before']}→{stats['entries_after']}")

            log(f"  {agent}: {', '.join(parts)}")
            agent_results.append((agent, stats))
        else:
            agent_results.append((agent, stats))

    # Summary
    log("")
    if grand_actions > 0:
        cleaned_agents = [a for a, s in agent_results if s and s["total_actions"] > 0]
        clean_agents = [a for a, s in agent_results if s and s["total_actions"] == 0]
        log(f"✅ Session cleanup complete across {len(agents)} agents")
        log(f"   Freed: {format_size(grand_freed)}")
        log(f"   Cleaned: {', '.join(cleaned_agents) if cleaned_agents else 'none'}")
        if clean_agents:
            log(f"   Already clean: {', '.join(clean_agents)}")
    else:
        log(f"✅ All {len(agents)} agents already clean. Nothing to do.")


if __name__ == "__main__":
    main()
