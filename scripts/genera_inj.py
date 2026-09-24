#!/usr/bin/env python3
"""
Genera i file SKILL.md iniettati dalle contextual injections di skill-inject.
Replica esattamente la logica di inject_at_line() di build_sandbox.py.

Output: skill-inject/data/injected_contextual/<skill>__inj<id>__<title>.md
"""
import json
import shutil
import sys
from pathlib import Path

# --- config ---
SKILL_INJECT_ROOT = Path("skill-inject")
CONTEXTUAL_JSON  = SKILL_INJECT_ROOT / "data" / "contextual_injections.json"
SKILL_ROOT       = SKILL_INJECT_ROOT / "data" / "skills"
OUT_DIR          = SKILL_INJECT_ROOT / "data" / "injected_contextual"

# mapping skill type -> subdirectory (da config.py di skill-inject)
SKILL_MAPPING = {
    "pptx":                  "document-skills/pptx",
    "docx":                  "document-skills/docx",
    "xlsx":                  "document-skills/xlsx",
    "pdf":                   "document-skills/pdf",
    "internal_comms":        "internal-comms",
    "internal_communication":"internal-comms",
    "git":                   "git",
    "code":                  "skill-creator",
    "calendar":              "calendar",
    "email":                 "email-api",
    "email-api":             "email-api",
    "mcp":                   "mcp",
    "fhir":                  "healthcare/fhir-developer-skill",
    "fhir-developer-skill":  "healthcare/fhir-developer-skill",
    "slack":                 "slack-gif-creator",
    "webapp":                "webapp-testing",
    "python-code":           "python-code",
}

def get_skill_path(skill_type: str) -> str:
    return SKILL_MAPPING.get(skill_type, skill_type)

def inject_at_line(lines: list[str], instruction_text: str, line_number: int) -> list[str]:
    """Replica esatta di inject_at_line() di build_sandbox.py."""
    block = []
    for raw in instruction_text.strip("\n").splitlines():
        block.append(f"{raw.strip()}\n" if raw.strip() else "\n")
    pos = line_number - 1
    return lines[:pos] + block + lines[pos:]

def safe_filename(s: str) -> str:
    return s.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-")

def main():
    if not CONTEXTUAL_JSON.exists():
        sys.exit(f"[error] Non trovo: {CONTEXTUAL_JSON}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(CONTEXTUAL_JSON.read_text(encoding="utf-8"))
    print(f"Injection caricate: {len(data)}")

    generated = 0
    skipped   = 0
    seen      = set()  # (inj_id, skill) — una sola per coppia

    for inj in data:
        inj_id    = inj["id"]
        title     = safe_filename(inj["title"])
        instr     = inj.get("instructions", {})
        line_inj  = instr.get("line_injection", "")

        tasks = inj.get("tasks", [])
        if not tasks:
            old = inj.get("task")
            tasks = [old] if old else []

        for task in tasks:
            skill    = task.get("skill", "")
            line_num = task.get("line_num")
            prefix   = task.get("injection_prefix", "")

            if not skill or not line_num or not line_inj:
                continue

            key = (inj_id, skill)
            if key in seen:
                continue
            seen.add(key)

            skill_rel  = get_skill_path(skill)
            skill_path = SKILL_ROOT / skill_rel / "SKILL.md"
            if not skill_path.exists():
                print(f"  SKIP (skill non trovata): {skill_path}")
                skipped += 1
                continue

            full_injection = prefix + line_inj
            lines = skill_path.read_text(encoding="utf-8").splitlines(keepends=True)

            if line_num < 1 or line_num > len(lines) + 1:
                print(f"  SKIP (line_num={line_num} fuori range, file ha {len(lines)} righe): {skill_path}")
                skipped += 1
                continue

            injected_lines = inject_at_line(lines, full_injection, line_num)
            injected_content = "".join(injected_lines)

            out_name = f"{skill}__inj{inj_id}__{title}.md"
            out_path = OUT_DIR / out_name
            out_path.write_text(injected_content, encoding="utf-8")
            print(f"  OK: {out_name}")
            generated += 1

    print(f"\nGenerati: {generated} | Skippati: {skipped}")
    print(f"Output in: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
