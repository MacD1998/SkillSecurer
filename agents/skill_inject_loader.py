"""
skill_inject_loader.py — carica le injection pre-costruite di skill-inject
==========================================================================
Per la pipeline `blue-eval`: legge i due JSON di skill-inject con injection
note (obvious / contextual), genera il SKILL.md iniettato replicando ESATTAMENTE
la logica di skill-inject (inject_at_line + SKILL_MAPPING di config.py), e
restituisce record con ground truth, così il Blue agent può essere valutato
contro injection note senza passare dal Red agent.

NB: SKILL_MAPPING e inject_at_line sono replicati 1:1 da skill-inject
(config.py::SKILL_MAPPING e scripts/build_sandbox.py::inject_at_line) per
garantire che il file iniettato sia byte-identico a quello che skill-inject
costruirebbe.
"""
from __future__ import annotations

import json
from pathlib import Path

import core.cli_output as cli


# ── Replica di skill-inject/config.py::SKILL_MAPPING ──────────────────
# Mantenere allineato a config.py. Mappa il tipo di skill (campo "skill" nei
# task JSON) alla sottocartella sotto data/skills/.
SKILL_MAPPING: dict[str, str] = {
    "pptx": "document-skills/pptx",
    "docx": "document-skills/docx",
    "xlsx": "document-skills/xlsx",
    "pdf": "document-skills/pdf",
    "internal_comms": "internal-comms",
    "internal_communication": "internal-comms",
    "git": "git",
    "code": "skill-creator",
    "calendar": "calendar",
    "email": "email-api",
    "email-api": "email-api",
    "mcp": "mcp",
    "fhir": "healthcare/fhir-developer-skill",
    "fhir-developer-skill": "healthcare/fhir-developer-skill",
    "slack": "slack-gif-creator",
    "webapp": "webapp-testing",
    "python-code": "python-code",
}


def get_skill_path(skill_type: str) -> str:
    """Mappa il tipo di skill alla sua sottocartella (replica di config.py)."""
    return SKILL_MAPPING.get(skill_type, skill_type)


def inject_at_line(base_content: str, instruction_text: str, line_number: int) -> str:
    """
    Inserisce instruction_text alla riga line_number (1-based) di base_content.

    Replica ESATTA di skill-inject/scripts/build_sandbox.py::inject_at_line, ma
    opera su stringhe (e ritorna la nuova stringa) invece di scrivere su file, e
    solleva ValueError invece di sys.exit su riga fuori range.
    """
    lines = base_content.splitlines(keepends=True)
    if line_number < 1 or line_number > len(lines) + 1:
        raise ValueError(
            f"line {line_number} out of range (file has {len(lines)} lines)")
    block: list[str] = []
    for raw in instruction_text.strip("\n").splitlines():
        block.append(f"{raw.strip()}\n" if raw.strip() else "\n")
    pos = line_number - 1
    return "".join(lines[:pos] + block + lines[pos:])


# Nome file target nelle skill di skill-inject (come build_sandbox: SKILL.md).
_TARGET_FILE = "SKILL.md"


def _resolve_base_file(skill_root: Path, skill_rel: str) -> Path | None:
    """SKILL.md sotto skills/<skill_rel>/ (fallback rglob, come resolve_target_file)."""
    direct = skill_root / skill_rel / _TARGET_FILE
    if direct.exists():
        return direct
    matches = list((skill_root / skill_rel).rglob(_TARGET_FILE))
    return matches[0] if len(matches) == 1 else None


_CATEGORY_FILES = {
    "obvious":    "obvious_injections.json",
    "contextual": "contextual_injections.json",
}


def load_records(
    skill_inject_path: Path,
    categories:        list[str],
    skills_filter:     list[str] | None = None,
    types_filter:      list[str] | None = None,
    max_files:         int | None = None,
) -> list[dict]:
    """
    Carica i record di injection da skill-inject per le categorie richieste.

    Args:
        skill_inject_path: root del repo skill-inject (contiene data/).
        categories:        sottoinsieme di {"obvious", "contextual"}.
        skills_filter:     se fornito, tiene solo i task il cui `skill` è in lista.
        types_filter:      se fornito, tiene solo le injection il cui `type` è in
                           lista (skill-inject categorizza per "script" | "direct").
        max_files:         se fornito, limita il numero TOTALE di record (cap globale,
                           utile per smoke test rapidi).

    Returns: lista di record (uno per coppia injection×task con line_injection):
        {injection_id, title, category, type, skill, skill_path,
         line_num, injected_text, injected_content, base_content}
    """
    data_dir   = skill_inject_path / "data"
    skill_root = data_dir / "skills"
    sf = set(skills_filter) if skills_filter else None
    tf = set(types_filter) if types_filter else None

    records: list[dict] = []
    # Dedup: la stessa injection può elencare task identici (stesso skill/line_num/
    # prefix), e injection diverse possono produrre lo stesso file iniettato. Blue
    # scansiona il FILE, quindi due task con stesso (skill, riga, testo) generano un
    # SKILL.md identico → scan ridondante che falsa le metriche (stessa injection
    # contata più volte) e spreca chiamate LLM. Teniamo solo il primo per chiave,
    # PRIMA di leggere la base e generare il file iniettato.
    seen_keys: set[tuple] = set()
    dup_skipped = 0
    for category in categories:
        jf = data_dir / _CATEGORY_FILES[category]
        if not jf.exists():
            cli.warn(f"[skill-inject] file non trovato: {jf}")
            continue
        try:
            injections = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            cli.warn(f"[skill-inject] parse fallito {jf.name}: {e}")
            continue

        for inj in injections:
            inj_id  = inj.get("id")
            title   = inj.get("title", "")
            itype   = inj.get("type", "")
            if tf is not None and itype not in tf:
                continue  # filtro per tipo injection (script/direct)
            instr   = inj.get("instructions", {}) or {}
            line_injection = instr.get("line_injection", "") or ""
            if not line_injection:
                continue  # nessuna line injection → niente da inserire a riga

            for task in (inj.get("tasks", []) or []):
                skill   = task.get("skill", "")
                line_num = task.get("line_num")
                prefix   = task.get("injection_prefix", "") or ""
                if not skill or not line_num:
                    continue
                if sf is not None and skill not in sf:
                    continue

                # Testo iniettato = prefix + line_injection (come build_sandbox).
                injected_text = (prefix + line_injection) if prefix else line_injection

                skill_rel = get_skill_path(skill)

                # Dedup PRIMA di leggere la base e generare il file: task con stesso
                # (skill target, riga, testo iniettato) producono un SKILL.md
                # byte-identico → scan ridondante. Saltarli qui evita la lettura
                # della base, inject_at_line e la successiva scrittura su disco.
                dedup_key = (skill_rel, str(line_num), injected_text)
                if dedup_key in seen_keys:
                    dup_skipped += 1
                    continue
                seen_keys.add(dedup_key)

                base_file = _resolve_base_file(skill_root, skill_rel)
                if base_file is None:
                    cli.warn(f"[skill-inject] SKILL.md non trovato per skill "
                             f"'{skill}' ({skill_rel}) — injection {category}-{inj_id} saltata")
                    continue

                base_content = base_file.read_text(encoding="utf-8", errors="ignore")
                try:
                    injected_content = inject_at_line(base_content, injected_text, int(line_num))
                except ValueError as e:
                    cli.warn(f"[skill-inject] {category}-{inj_id}/{skill}: {e} — saltata")
                    continue

                records.append({
                    "injection_id":     f"{category}-{inj_id}",
                    "title":            title,
                    "category":         category,
                    "type":             itype,
                    "skill":            skill,
                    "skill_path":       str(base_file),
                    "line_num":         int(line_num),
                    "injected_text":    injected_text,
                    "injected_content": injected_content,
                    "base_content":     base_content,
                })

    if dup_skipped:
        cli.debug(f"  ↳ skill-inject: {dup_skipped} duplicate injection(s) skipped "
                  f"before file generation (identical injected file) → {len(records)} unique")

    if max_files and max_files > 0:
        records = records[:max_files]
    return records
