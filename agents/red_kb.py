"""
red_kb.py — knowledge base skill-inject per il Red agent (profilo paper)
========================================================================
Costruisce, dalle injection direct di skill-inject (obvious + contextual), una
KB raggruppata per classe di danno del paper. Serve come *ispirazione* al Red:
esempi reali della classe che sta generando, con il vincolo di produrne di
DIVERSI (mai copiati).

Le 68 injection direct non hanno una label di classe nei dati di skill-inject:
la mappa injection_id → classe vive in config/skill_inject_kb_labels.json
(hand-labeled, allineata alle 8 classi del paper).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import core.cli_output as cli

DEFAULT_LABELS = Path(__file__).parent.parent / "config" / "skill_inject_kb_labels.json"

# Soglia Jaccard (token) oltre cui due esempi sono considerati near-duplicate e
# uno viene scartato. skill-inject ha varianti-template quasi identiche (stessa
# injection su skill diverse) → gonfiano il prompt senza aggiungere meccanismi.
_DEDUP_JACCARD = 0.8


def _tokset(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _dedup_class(items: list[dict]) -> list[dict]:
    """Greedy: tiene il primo esempio, scarta i successivi troppo simili (Jaccard
    > soglia) a uno già tenuto. Preserva l'ordine (obvious prima, poi contextual)."""
    kept: list[dict] = []
    kept_toks: list[set[str]] = []
    for e in items:
        t = _tokset(e.get("text", ""))
        if not t:
            continue
        if any((len(t & kt) / len(t | kt)) > _DEDUP_JACCARD for kt in kept_toks):
            continue
        kept.append(e)
        kept_toks.append(t)
    return kept


def build_kb(
    skill_inject_path: Path,
    labels_path:       Path = DEFAULT_LABELS,
    categories:        list[str] | None = None,
) -> dict[str, list[dict]]:
    """
    Ritorna {classe_paper: [{"id", "skill", "text"}, ...]}.

    Args:
        skill_inject_path: root del repo skill-inject (contiene data/).
        labels_path:       JSON injection_id → classe.
        categories:        sottoinsieme di {"obvious","contextual"} (default: entrambe).

    La KB è deduplicata per injection_id (una injection compare su più task/skill:
    teniamo il primo testo e collezioniamo le skill in cui appare).
    """
    from agents.skill_inject_loader import load_records

    cats = categories or ["obvious", "contextual"]
    try:
        labels = json.loads(labels_path.read_text(encoding="utf-8")).get("labels", {})
    except Exception as e:
        cli.warn(f"[red-kb] labels non leggibili {labels_path}: {e}")
        return {}

    records = load_records(skill_inject_path, cats, types_filter=["direct"])

    seen: dict[str, dict] = {}
    unlabeled: set[str] = set()
    for r in records:
        inj_id = r.get("injection_id", "")
        cls    = labels.get(inj_id)
        if not cls:
            unlabeled.add(inj_id)
            continue
        if inj_id in seen:
            seen[inj_id]["skills"].add(r.get("skill", ""))
            continue
        seen[inj_id] = {
            "id":     inj_id,
            "class":  cls,
            "skills": {r.get("skill", "")},
            "text":   (r.get("injected_text", "") or "").strip(),
        }

    kb: dict[str, list[dict]] = {}
    for item in seen.values():
        kb.setdefault(item["class"], []).append({
            "id":    item["id"],
            "skill": next(iter(item["skills"]), ""),
            "text":  item["text"],
        })

    # Dedup near-duplicate per classe (varianti-template skill-inject).
    n_before = sum(len(v) for v in kb.values())
    kb = {c: _dedup_class(v) for c, v in kb.items()}
    n_after = sum(len(v) for v in kb.values())

    if unlabeled:
        cli.warn(f"[red-kb] {len(unlabeled)} injection senza label in {labels_path.name} "
                 f"(saltate): {sorted(unlabeled)[:8]}...")
    # info (non debug) → sempre visibile a log: evidenza che la KB skill-inject è attiva.
    _dd = f" (dedup: {n_before}→{n_after}, -{n_before - n_after})" if n_after < n_before else ""
    cli.info(f"  📚 [red-kb] KB skill-inject attiva: "
             f"{n_after} esempi su {len(kb)} classi{_dd} "
             f"({', '.join(sorted(kb))})")
    return kb
