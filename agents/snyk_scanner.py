"""
Snyk Scanner
============
Wrapper attorno a `snyk-agent-scan` (Snyk Labs, https://github.com/snyk/agent-scan),
lanciato via `uvx` per confrontare i finding del Blue agent con un motore terzo.

Snyk documenta lo schema JSON dell'output come "experimental and may change without
notice" — il parsing qui è quindi difensivo: prova più chiavi note, e se proprio non
riesce a interpretare l'output non solleva mai, restituisce scan_error + raw.

Output:
{
  "findings":   list[dict],   # {"code", "severity", "title", "description", "quote"}
  "scan_error": str | None,   # motivo del fallimento (uvx assente, timeout, ...)
  "raw":        dict | str | None,  # output grezzo (parsed JSON, o stdout troncato)
  "source":     "live" | "skills_sh_audit",  # da dove viene il verdetto
}
"""
import json
import subprocess
from pathlib import Path
from typing import Optional

SCAN_TIMEOUT = 120
_RAW_TRUNCATE = 4000

# Chiavi note sotto cui l'output di `snyk-agent-scan --json` può annidare la lista
# di finding — lo schema non è garantito stabile tra versioni del tool.
_FINDING_LIST_KEYS = ("findings", "issues", "results")


def _normalize_finding(raw: dict) -> dict:
    # Forma reale osservata (v0.5.15, `--json`): {"code","message","extra_data":
    # {"severity","title","evidence","reason","description",...}}. severity/title
    # vivono sotto extra_data, non al top level — solo code/message ci sono.
    extra = raw.get("extra_data") or {}
    return {
        "code":        raw.get("code") or raw.get("id") or raw.get("rule") or "",
        "severity":    (extra.get("severity") or raw.get("severity") or raw.get("level") or "").lower(),
        "title":       extra.get("title") or raw.get("title") or raw.get("name") or "",
        "description": raw.get("message") or extra.get("reason")
                        or extra.get("description") or raw.get("description") or raw.get("detail") or "",
        "quote":       extra.get("evidence") or "",
    }


def _extract_findings(parsed, _depth: int = 0) -> list[dict]:
    """Cerca una lista di finding sotto le chiavi note, a qualunque profondità.
    Forma reale osservata: {"<scanned-path>": {"issues": [...], ...}} — la lista
    di finding sta annidata sotto un dict con chiave dinamica (il path scansionato),
    quindi si scende SOLO dentro i valori dict (mai dentro liste generiche come
    "servers"/"labels", che conterrebbero dict non-finding e darebbero falsi
    positivi se normalizzati alla cieca). _depth taglia la ricorsione per
    sicurezza su output inatteso."""
    if _depth > 6 or not isinstance(parsed, (dict, list)):
        return []

    if isinstance(parsed, dict):
        for key in _FINDING_LIST_KEYS:
            val = parsed.get(key)
            if isinstance(val, list):
                return [_normalize_finding(f) for f in val if isinstance(f, dict)]
        findings: list[dict] = []
        for val in parsed.values():
            if isinstance(val, dict):
                findings.extend(_extract_findings(val, _depth + 1))
        return findings

    # parsed è una list (top-level o annidata) non raggiunta via una chiave nota:
    # cerca dentro ogni elemento dict, invece di assumere che la lista STESSA sia
    # la lista di finding (eviterebbe di normalizzare "servers"/"labels" come finding).
    nested: list[dict] = []
    for item in parsed:
        if isinstance(item, dict):
            nested.extend(_extract_findings(item, _depth + 1))
    if nested:
        return nested
    # Fallback: nessuna chiave nota annidata, ma gli elementi hanno la forma di un
    # finding grezzo (code/message) → trattali come lista di finding diretta.
    if parsed and all(isinstance(it, dict) and ("code" in it or "message" in it) for it in parsed):
        return [_normalize_finding(f) for f in parsed]
    return nested


def _find_scan_error(parsed, _depth: int = 0) -> Optional[str]:
    """Cerca un errore di scan annidato (es. `servers[].error = {"exception":
    "429, Too Many Requests", "message": "Daily usage limit reached..."}`).

    Osservato empiricamente: quando l'endpoint cloud di Snyk rate-limita o nega
    per quota esaurita, il tool lo INGOIA — il campo error di livello top resta
    `null` e l'exit code è 0, ma issues finisce vuoto. Senza questo controllo
    quel fallimento verrebbe scambiato per uno scan pulito (falso negativo su un
    tool di sicurezza). Qui lo intercettiamo scendendo nella struttura annidata."""
    if _depth > 6 or not isinstance(parsed, (dict, list)):
        return None
    if isinstance(parsed, dict):
        err = parsed.get("error")
        if isinstance(err, dict) and ("exception" in err or "message" in err):
            msg = err.get("message") or err.get("exception") or "errore sconosciuto lato Snyk"
            return str(msg)[:500]
        for val in parsed.values():
            if isinstance(val, (dict, list)):
                found = _find_scan_error(val, _depth + 1)
                if found:
                    return found
        return None
    for item in parsed:
        found = _find_scan_error(item, _depth + 1)
        if found:
            return found
    return None


def _normalize_audit_issue(raw: dict) -> dict:
    # Forma di skills_sh_dataset/out/skills/<owner>__<repo>__<skillId>/meta.json,
    # campo audit_full.snyk.result.issues[] — scraping dell'audit pubblico di
    # skills.sh, stesso motore ma NON uno scan live (niente "extra_data" annidato,
    # code/severity/description/message/reason sono già al livello giusto).
    return {
        "code":        raw.get("code") or "",
        "severity":    (raw.get("severity") or "").lower(),
        "title":       raw.get("description") or raw.get("code") or "",
        "description": raw.get("message") or raw.get("reason") or raw.get("description") or "",
    }


def _lookup_skills_sh_audit(skill_path: str) -> Optional[dict]:
    """Se `skill_path` fa parte del dataset skills_sh_dataset (ha un meta.json
    accanto con un audit Snyk già scraperato da skills.sh), usa quel verdetto
    invece di lanciare uno scan live — zero consumo di quota, stessa fonte dati
    (Snyk), verdetto pre-calcolato. Ritorna None se non applicabile (file fuori
    dataset, o meta.json senza sezione snyk) → run() farà lo scan live come al
    solito."""
    meta_path = Path(skill_path).with_name("meta.json")
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None

    snyk = ((meta.get("audit_full") or {}).get("snyk") or {}).get("result")
    if not isinstance(snyk, dict):
        return None

    issues = snyk.get("issues") or []
    findings = [_normalize_audit_issue(i) for i in issues if isinstance(i, dict)]
    return {"findings": findings, "scan_error": None, "raw": snyk, "source": "skills_sh_audit"}


def _scan_once(skill_path: str) -> dict:
    try:
        result = subprocess.run(
            # Path posizionale (CONFIG_FILE): la CLI auto-rileva un SKILL.md e lo
            # scansiona come skill. `--skills`/`--no-skills` è un toggle booleano
            # (default: enabled) — NON prende un path, va passato solo un file.
            ["uvx", "snyk-agent-scan@latest", skill_path, "--json", "--print-errors"],
            capture_output=True, text=True, timeout=SCAN_TIMEOUT,
        )
    except FileNotFoundError:
        return {"findings": [], "scan_error": "uvx non trovato — installa uv per abilitare il confronto Snyk.", "raw": None, "source": "live"}
    except subprocess.TimeoutExpired:
        return {"findings": [], "scan_error": f"snyk-agent-scan timeout dopo {SCAN_TIMEOUT}s", "raw": None, "source": "live"}
    except Exception as e:
        return {"findings": [], "scan_error": f"snyk-agent-scan errore: {e}", "raw": None, "source": "live"}

    stdout = (result.stdout or "").strip()
    if result.returncode != 0 and not stdout:
        err = (result.stderr or "").strip()[:_RAW_TRUNCATE]
        # In modalità non-verbose la CLI fallisce spesso senza stampare nulla
        # quando manca SNYK_TOKEN — segnaliamo esplicitamente questo caso comune.
        if not err:
            err = "nessun output (verifica che SNYK_TOKEN sia impostato — vedi https://app.snyk.io/account)"
        return {"findings": [], "scan_error": f"snyk-agent-scan exit={result.returncode}: {err}", "raw": None, "source": "live"}

    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return {
            "findings": [],
            "scan_error": "unparsed output",
            "raw": stdout[:_RAW_TRUNCATE],
            "source": "live",
        }

    scan_err = _find_scan_error(parsed)
    if scan_err:
        return {"findings": [], "scan_error": f"Snyk analysis error: {scan_err}", "raw": parsed, "source": "live"}

    findings = _extract_findings(parsed)
    return {"findings": findings, "scan_error": None, "raw": parsed, "source": "live"}


def run(skill_path: str) -> dict:
    """Esegue `uvx snyk-agent-scan@latest <skill_path> --json` e normalizza l'output.
    Non solleva mai: errori/timeout/parsing falliti finiscono in scan_error.

    Retry singolo, SOLO quando lo scan segnala un errore esplicito (quota Snyk
    esaurita — HTTP 429 "Daily usage limit reached...", intercettato da
    _find_scan_error — timeout, parsing fallito, ecc.): un secondo tentativo ha
    ragionevoli probabilità di recuperare un errore transitorio.

    Prima ritentava incondizionatamente ogni volta che `findings` era vuoto,
    ANCHE senza alcun errore — pensato per coprire un'ulteriore modalità di
    guasto osservata empiricamente (l'endpoint degrada silenziosamente sotto
    scan concorrenti e torna "issues": [] con exit=0, indistinguibile a livello
    locale da uno scan pulito riuscito, "non riproducibile in isolamento").
    Il problema: quella modalità è rara, mentre "skill davvero pulita, nessun
    errore" è la maggioranza dei casi — il retry incondizionato raddoppiava le
    chiamate/quota Snyk proprio sul path più comune, per coprire un caso raro e
    comunque non distinguibile con certezza nemmeno DOPO il retry. Nessun altro
    scanner terzo di questo progetto raddoppia sul path pulito; qui ora nemmeno.
    Un errore esplicito resta un segnale concreto e vale un secondo tentativo,
    un "findings=[] senza errore" ora è preso alla lettera (probabile scan pulito).

    Se il file fa parte di skills_sh_dataset (meta.json con audit Snyk già
    scraperato accanto al SKILL.md), usa quel verdetto e salta lo scan live."""
    cached = _lookup_skills_sh_audit(skill_path)
    if cached is not None:
        return cached

    res = _scan_once(skill_path)
    if res["scan_error"]:
        retry = _scan_once(skill_path)
        if not retry["scan_error"]:
            return retry
    return res
