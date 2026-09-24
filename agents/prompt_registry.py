"""
Prompt registry
===============
Punto unico per (a) mostrare nel report.html il system prompt EFFETTIVO usato da
ogni agente e (b) renderlo parametrizzabile al lancio di un run dalla WebUI.

Meccanica override (attraversa il confine di processo main.py):
  - la WebUI scrive un file JSON {name: testo} e ne mette il path in env
    SSE3_PROMPT_OVERRIDES.
  - ogni agente chiede il proprio prompt via resolve(name, DEFAULT): se esiste un
    override per quel name lo usa, altrimenti il default hard-coded nel modulo.
  - assente/vuoto ⇒ tutti i default (comportamento storico invariato).

Niente import di moduli-agente a livello di modulo: gli agenti importano solo
resolve() (leggero), mentre default_prompts()/active_prompts() importano i moduli
in modo lazy — nessun ciclo di import.
"""
from __future__ import annotations

import functools
import json
import os
from pathlib import Path


# name → (label mostrata, modulo, attributo) per i prompt STATICI.
# Il Red è dinamico (derivato dal catalog) → gestito a parte.
_STATIC: list[tuple[str, str, str, str]] = [
    ("blue_scan",    "Blue · scan",         "agents.blue_agent",        "SCAN_PROMPT"),
    ("blue_patch",   "Blue · patch",        "agents.blue_agent",        "PATCH_PROMPT"),
    ("eval",         "Eval (detection audit)", "agents.blue_eval_judge", "_SYSTEM"),
    ("judge",        "Judge (ASR)",         "agents.judge_agent",       "SYSTEM_PROMPT"),
    ("tester_judge", "Tester · task judge", "agents.tester_agent",      "_TASK_JUDGE_SYSTEM"),
    ("environment",  "Environment",         "agents.environment_agent", "_SYS"),
]

_RED_LABEL = "Red (injection generator)"


# ── Override lato agente ───────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def _overrides() -> dict:
    """Carica gli override dal file JSON in env SSE3_PROMPT_OVERRIDES (cache)."""
    path = (os.environ.get("SSE3_PROMPT_OVERRIDES") or "").strip()
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if isinstance(v, str) and v.strip()}
    except Exception:
        return {}


def resolve(name: str, default: str) -> str:
    """Prompt effettivo per `name`: override se presente e non vuoto, altrimenti default."""
    return _overrides().get(name) or default


# ── Default / attivi (lato report + WebUI) ─────────────────────────────
def _static_default(module: str, attr: str) -> str:
    import importlib
    return getattr(importlib.import_module(module), attr)


def _red_default(catalog: dict | None = None) -> str:
    from agents.red_agent import _system_prompt, load_catalog
    if catalog is None:
        catalog = load_catalog()
    return _system_prompt(catalog)


def default_prompts(catalog: dict | None = None) -> list[dict]:
    """Lista ordinata {name, label, text} dei prompt DI DEFAULT (per prefill UI)."""
    out = [{"name": "red", "label": _RED_LABEL, "text": _red_default(catalog)}]
    for name, label, module, attr in _STATIC:
        try:
            out.append({"name": name, "label": label, "text": _static_default(module, attr)})
        except Exception:
            continue
    return out


def active_prompts(red_prompt: str | None = None, catalog: dict | None = None,
                   names: list[str] | None = None) -> list[dict]:
    """Lista ordinata {name, label, text} dei prompt EFFETTIVI (override applicati).

    red_prompt: se il chiamante ha già il system prompt del Red calcolato col
    catalog reale del run (es. data['red_system_prompt']), passarlo qui evita di
    ricalcolarlo; è già post-override lato agente. Altrimenti si ricava dal catalog.
    names: se dato, filtra ai soli agenti indicati (ordine canonico preservato) —
    così il report mostra SOLO gli agenti effettivamente usati nel run.
    """
    keep = set(names) if names is not None else None
    out: list[dict] = []
    if keep is None or "red" in keep:
        red = red_prompt if red_prompt else resolve("red", _red_default(catalog))
        out.append({"name": "red", "label": _RED_LABEL, "text": red})
    for name, label, module, attr in _STATIC:
        if keep is not None and name not in keep:
            continue
        try:
            out.append({"name": name, "label": label,
                        "text": resolve(name, _static_default(module, attr))})
        except Exception:
            continue
    return out
