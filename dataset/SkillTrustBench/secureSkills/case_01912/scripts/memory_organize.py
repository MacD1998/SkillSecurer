#!/usr/bin/env python3
"""memory_organize.py

Deterministic memory organizer for OpenClaw.

Moves *.md files from memory/ root into topic subfolders, adds lightweight
frontmatter, and updates topic INDEX.md tables.

Design goals:
- No LLM dependency (fast, predictable)
- Idempotent (safe to run daily)
- Conservative edits (never overwrite existing frontmatter)

Exit codes:
  0 = success
  2 = nothing to do
  1 = error
"""

from __future__ import annotations

import os
import re
import sys

try:
    import fcntl  # type: ignore
except Exception:
    fcntl = None

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

WS = Path.home() / ".openclaw" / "workspace"
MEMORY = WS / "memory"
LOCK_DIR = WS / ".locks"
LOCK_FILE = LOCK_DIR / "memory_organize.lock"

TOPICS = ["cabinet", "content", "products", "technical", "user", "x", "daily"]

# Keyword routing rules (lowercase)
ROUTES: List[Tuple[str, List[str]]] = [
    ("cabinet", ["agent", "cron", "delegation", "cabinet", "aegis", "atlas", "echo", "clio", "argus", "vera", "quill"]),
    ("content", ["post", "blog", "marketing", "seo", "newsletter", "clip", "clips", "postiz"]),
    ("products", ["copanion", "hypercho", "feature", "ui", "ux", "product", "roadmap", "release"]),
    ("technical", ["bug", "error", "config", "docs", "openclaw", "gateway", "build", "ci", "json", "sitemap"]),
    ("x", ["twitter", "x.com", "viral", "engagement", "impressions", "followers"]),
    ("user", ["ziwen", "founder", "personal", "preference"]),
]


@dataclass
class Plan:
    src: Path
    topic: str
    date: Optional[str]
    tags: List[str]
    description: str


def _slug_date_from_name(name: str) -> Optional[str]:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else None


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _has_frontmatter(text: str) -> bool:
    # very lightweight: starts with --- on first line
    return text.lstrip().startswith("---\n")


def _extract_description(text: str) -> str:
    # First non-empty line that isn't frontmatter or a markdown title marker.
    lines = [ln.rstrip() for ln in text.splitlines()]

    # Skip frontmatter if present
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i = min(i + 1, len(lines))

    for ln in lines[i:]:
        s = ln.strip()
        if not s:
            continue
        s = re.sub(r"^#+\s*", "", s).strip()
        if not s:
            continue
        # cap
        return (s[:77] + "…") if len(s) > 78 else s

    return "(auto)"


def _choose_topic(name: str, text: str) -> str:
    hay = f"{name}\n{text}".lower()
    for topic, kws in ROUTES:
        if any(kw in hay for kw in kws):
            return topic
    return "daily"


def _tags_for(topic: str, name: str, text: str) -> List[str]:
    hay = f"{name}\n{text}".lower()
    tags = {topic}

    # a few useful cross-tags
    if "timeout" in hay or "timed out" in hay:
        tags.add("timeout")
    if "browser" in hay or "relay" in hay:
        tags.add("browser")
    if "post" in hay or "blog" in hay:
        tags.add("blog")
    if "clip" in hay:
        tags.add("clips")
    if "openclaw" in hay:
        tags.add("openclaw")

    # keep stable order
    return sorted(tags)


def _ensure_topic_dir(topic: str) -> Path:
    d = MEMORY / topic
    d.mkdir(parents=True, exist_ok=True)
    return d


def _add_frontmatter_if_missing(text: str, *, topic: str, date: Optional[str], tags: List[str]) -> str:
    if _has_frontmatter(text):
        return text

    # Minimal frontmatter
    date_line = f"date: {date}" if date else f"date: {datetime.now().date().isoformat()}"
    tags_line = "tags: [" + ", ".join(tags) + "]"
    fm = "---\n" + f"topic: {topic}\n" + date_line + "\n" + tags_line + "\n---\n\n"
    return fm + text.lstrip("\n")


def _update_index(topic_dir: Path, *, filename: str, description: str) -> None:
    idx = topic_dir / "INDEX.md"
    if not idx.exists():
        # create a minimal index if missing
        idx.write_text(
            f"# {topic_dir.name.title()}\n\n## Files\n\n| File | Description |\n|------|-------------|\n",
            encoding="utf-8",
        )

    s = _read_text(idx)
    if f"`{filename}`" in s:
        return  # already indexed

    lines = s.splitlines()

    # Find the files table header separator
    sep_i = None
    for i, ln in enumerate(lines):
        if ln.strip() == "|------|-------------|":
            sep_i = i
            break

    new_row = f"| `{filename}` | {description} |"

    if sep_i is None:
        # append a new table at end
        lines += ["", "## Files", "", "| File | Description |", "|------|-------------|", new_row]
    else:
        # insert after the last existing table row following the separator
        insert_at = sep_i + 1
        while insert_at < len(lines) and lines[insert_at].startswith("|"):
            insert_at += 1
        lines.insert(insert_at, new_row)

    idx.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def plan_for_file(p: Path) -> Plan:
    text = _read_text(p)
    date = _slug_date_from_name(p.name)
    topic = _choose_topic(p.name, text)
    tags = _tags_for(topic, p.name, text)
    desc = _extract_description(text)
    return Plan(src=p, topic=topic, date=date, tags=tags, description=desc)


def iter_root_md_files() -> Iterable[Path]:
    for p in sorted(MEMORY.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        yield p


def main() -> int:
    # Prevent concurrent runs (e.g., launchd + OpenClaw cron at the same minute).
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    if fcntl is not None:
        with open(LOCK_FILE, "w") as lf:
            try:
                fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("Already running")
                return 0

            return _main_locked()

    # If fcntl unavailable, proceed without lock (best effort).
    return _main_locked()


def _main_locked() -> int:
    if not MEMORY.exists():
        print(f"ERROR: memory dir not found: {MEMORY}")
        return 1

    files = list(iter_root_md_files())
    if not files:
        print("Nothing to do")
        return 2

    moved = 0
    for p in files:
        plan = plan_for_file(p)
        topic_dir = _ensure_topic_dir(plan.topic)
        dest = topic_dir / plan.src.name

        # Add frontmatter in-place BEFORE move, so move is atomic afterwards.
        txt = _read_text(plan.src)
        new_txt = _add_frontmatter_if_missing(txt, topic=plan.topic, date=plan.date, tags=plan.tags)
        if new_txt != txt:
            plan.src.write_text(new_txt, encoding="utf-8")

        # Move (replace if destination exists with identical name)
        if dest.exists():
            # avoid overwriting: add suffix
            stem = dest.stem
            suf = dest.suffix
            k = 2
            while True:
                cand = topic_dir / f"{stem}--{k}{suf}"
                if not cand.exists():
                    dest = cand
                    break
                k += 1

        plan.src.replace(dest)
        _update_index(topic_dir, filename=dest.name, description=plan.description)
        moved += 1

    print(f"Memory organization complete: moved {moved} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
