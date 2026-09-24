"""
skills.sh Comparison Scanner
============================
Non è uno scan live: legge il verdetto GIÀ presente nel `meta.json` scaricato
da skills_sh_dataset (vedi skills_sh_dataset/ — scraper delle skill pubbliche
di skills.sh + i loro audit). skills.sh fa girare 3 motori indipendenti per
ogni skill (agentTrustHub, socket, snyk) — qui li normalizziamo nello stesso
schema {code,severity,title,description,quote} di snyk_scanner/
skillspector_scanner, uno per motore, più un flag aggregato `any_flagged`
(OR sui 3 motori disponibili).

Include ANCHE la normalizzazione dello snyk di skills.sh (non solo delega al
toggle "Compare with Snyk" — snyk_scanner._lookup_skills_sh_audit legge la
STESSA fonte quando punta a un file di questo dataset, ma qui serve comunque
per calcolare `any_flagged` senza dipendere da un altro toggle attivo).

Nessuna chiamata di rete/subprocess: run() legge solo il meta.json locale già
scaricato accanto al file scansionato → costo prossimo a zero, può girare in
parallelo al Blue esattamente come Snyk (anzi più leggero: zero I/O di rete).

Output:
{
  "available":   bool,  # False se non c'è un meta.json con audit_full accanto
                         # al file (skill fuori dal dataset skills.sh)
  "engines": {
     "snyk":          {"flagged": bool, "findings": list[dict]},
     "socket":        {"flagged": bool, "findings": list[dict]},
     "agentTrustHub": {"flagged": bool, "findings": list[dict]},
  },
  "any_flagged": bool,  # OR sui motori disponibili
}
"""
import json
from pathlib import Path
from typing import Optional


def _normalize_snyk(result: dict) -> dict:
    issues = result.get("issues") or []
    findings = [{
        "code":        i.get("code") or "",
        "severity":    (i.get("severity") or "").lower(),
        "title":       i.get("description") or i.get("code") or "",
        "description": i.get("message") or i.get("reason") or "",
        "quote":       "",
    } for i in issues if isinstance(i, dict)]
    return {"flagged": bool(findings), "findings": findings}


def _normalize_socket(result: dict) -> dict:
    # alert.severity osservato: "low"/"middle"/"high" — non un enum fisso, si
    # passa così com'è (lowercased) invece di forzare un mapping rigido.
    alerts = result.get("alerts") or []
    findings = []
    for a in alerts:
        if not isinstance(a, dict):
            continue
        props = a.get("props") or {}
        findings.append({
            "code":        a.get("type") or "",
            "severity":    (a.get("severity") or "").lower(),
            "title":       a.get("category") or a.get("type") or "",
            "description": props.get("notes") or "",
            "quote":       "",
        })
    return {"flagged": bool(findings), "findings": findings}


def _normalize_agent_trust_hub(result: dict) -> dict:
    findings = []

    # 1) Findings statici (AST/regex) su file del repo — evidence è la citazione
    #    reale (riga del match), come per skillspector.
    ca = result.get("content_analysis") or {}
    for f in ca.get("static_security_findings") or []:
        if not isinstance(f, dict):
            continue
        loc = f.get("file_path") or ""
        line = f.get("line_number")
        findings.append({
            "code":        f.get("rule_id") or "",
            "severity":    (f.get("severity") or "").lower(),
            "title":       f.get("title") or "",
            "description": f"{loc}:{line}" if loc and line else loc,
            "quote":       f.get("evidence") or "",
        })

    # 2) Antivirus sui file della skill (rarissimo, ma da mostrare se capita).
    av = result.get("av_analysis") or {}
    for r in av.get("results") or []:
        if not isinstance(r, dict) or (r.get("verdict") or "clean") == "clean":
            continue
        # detections: osservato sia list[str] che list[dict] (con detection_name/
        # type_name) a seconda del motore AV sottostante — normalizzo entrambi.
        det_names = [
            (d.get("detection_name") or d.get("type_name") or str(d)) if isinstance(d, dict) else str(d)
            for d in (r.get("detections") or [])
        ]
        findings.append({
            "code":        "AV",
            "severity":    "high",
            "title":       f"Antivirus: {r.get('filename') or '?'}",
            "description": ", ".join(det_names) or (r.get("verdict") or ""),
            "quote":       "",
        })

    # 3) Verdetto semantico LLM (Gemini) — nessun match statico ancorato, stessa
    #    situazione dei finding puramente semantici di SkillSpector: solo
    #    verdict/summary, mai una quote. LOW trattato come "clean" (stesso
    #    criterio usato per gli altri due motori: bassa severità = non flaggato).
    g = result.get("gemini_analysis") or {}
    verdict = (g.get("verdict") or "").upper()
    if verdict in ("MEDIUM", "HIGH", "CRITICAL"):
        findings.append({
            "code":        ",".join(g.get("categories") or []) or "GEMINI",
            "severity":    verdict.lower(),
            "title":       "Gemini semantic analysis",
            "description": g.get("summary") or "",
            "quote":       "",
        })

    return {"flagged": bool(findings), "findings": findings}


_NORMALIZERS = {
    "snyk":          _normalize_snyk,
    "socket":        _normalize_socket,
    "agentTrustHub": _normalize_agent_trust_hub,
}


def _find_meta_json(skill_path: str) -> Optional[Path]:
    """meta.json vive accanto al SKILL.md scaricato da skills_sh_dataset (stessa
    convenzione già usata da agents/snyk_scanner.py: _lookup_skills_sh_audit)."""
    meta_path = Path(skill_path).with_name("meta.json")
    return meta_path if meta_path.exists() else None


def run(skill_path: str) -> dict:
    """Legge audit_full dal meta.json accanto a skill_path. Non solleva mai —
    se il file è fuori dal dataset skills.sh (nessun meta.json, o senza
    audit_full) torna available=False, distinguibile da un vero 'clean'."""
    meta_path = _find_meta_json(skill_path)
    if meta_path is None:
        return {"available": False, "engines": {}, "any_flagged": False}

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {"available": False, "engines": {}, "any_flagged": False}

    audit_full = meta.get("audit_full")
    if not isinstance(audit_full, dict) or not audit_full:
        return {"available": False, "engines": {}, "any_flagged": False}

    engines: dict[str, dict] = {}
    for name, normalize in _NORMALIZERS.items():
        entry = audit_full.get(name)
        if not isinstance(entry, dict):
            continue
        result = entry.get("result")
        if not isinstance(result, dict):
            continue
        engines[name] = normalize(result)

    any_flagged = any(e["flagged"] for e in engines.values())
    return {"available": bool(engines), "engines": engines, "any_flagged": any_flagged}
