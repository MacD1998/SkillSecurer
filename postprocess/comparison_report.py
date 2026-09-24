"""
comparison_report.py — report comparativo su N run che condividono il dataset.
==============================================================================
Generalizzazione di results/scanner_in_the_wild_1000/make_comparison_report.py
(nato per il caso "Blue vs le 3 audit engine di skills.sh" dentro UNA run) a un
numero qualsiasi di colonne-motore prese da run diverse:

  colonna = (run, motore)   — es. (scanner_selection_26_verified_Blue, blue),
                                  (scanner_selection_26_verified_Tencent_aig, aig)

Le run vengono joinate per caso con `run_index.case_key` (stesso file di input).
Un motore che espone `meta.sub_engines` (skills_sh → snyk/socket/agentTrustHub)
viene sostituito dalle sue sotto-engine: passando la sola run in-the-wild si
riottiene esattamente il report originale (Blue + Snyk + Socket + AgentTrustHub).

Riferimento (`ref`): la colonna contro cui tutte le altre sono confrontate —
default la prima colonna `blue`, altrimenti la prima in assoluto. L'aggregato
"any" è "flaggato da almeno una delle altre colonne".

Uso:
  python3 -m postprocess.comparison_report --runs results/a results/b \\
      --output results/cmp_ab [--ref results/a:blue] [--title "..."]

Scrive <output>/comparison_report.html (interattivo: tassonomia editabile per
finding, filtri, ricerca, sort) + <output>/comparison_data.json (aggregati).
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from postprocess.run_index import case_key

BASE = Path(__file__).resolve().parent.parent

# ── Etichette motori note ────────────────────────────────────────────────
ENGINE_LABEL = {
    "blue":          "Blue (ours)",
    "skills_sh":     "skills.sh (any)",
    "snyk":          "Snyk",
    "socket":        "Socket",
    "agentTrustHub": "AgentTrustHub",
    "cisco":         "Cisco SkillScanner",
    "skillspector":  "NVIDIA SkillSpector",
    "aig":           "Tencent AIG",
    "skill_vetter":  "skill-vetter",
}

# Palette: --s1 al riferimento, --s2 all'aggregato, --s3+ alle altre colonne.
OTHER_COLORS = ["--s3", "--s4", "--s5", "--s6", "--s7", "--s8", "--s9", "--s10"]

# ── Finding taxonomy (vedi Finding_Taxonomy.md) ──────────────────────────
# Provenance e classe ASI sono auto-classificate per finding dal codice/tipo
# del motore + testo, poi editabili per-finding nella UI del report.
PROVENANCE_LABELS = ["INJECTED", "PRE_EXISTING", "CONFIGURATION", "AMBIGUOUS"]
ASI_LABELS = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse & Exploitation",
    "ASI03": "Identity & Privilege Abuse",
    "ASI04": "Agentic Supply-Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution",
    "ASI06": "Memory & Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}

BLUE_TYPE_MAP = {
    "arbitrary_code_execution": (None, ("ASI05", "ASI02")),
    "prompt_injection": (None, ("ASI01", "ASI09")),
    "data_exfiltration": (None, ("ASI02", "ASI03")),
    "credential_exposure": (None, ("ASI03", "ASI02")),
    "command_injection": (None, ("ASI05", "ASI02")),
    "privilege_escalation": (None, ("ASI03", "ASI02")),
    "path_traversal": (None, ("ASI02", "ASI05")),
    "insecure_configuration": ("CONFIGURATION", ()),
    "cross_site_scripting": (None, ("ASI05", "ASI02")),
    "arbitrary_file_write": (None, ("ASI05", "ASI02")),
    "ssrf": (None, ("ASI02", "ASI04")),
    "server_side_request_forgery": (None, ("ASI02", "ASI04")),
    "safety_bypass": (None, ("ASI01", "ASI09")),
    "code_injection": (None, ("ASI05", "ASI02")),
    "injection": (None, ("ASI01",)),
    "insecure_design": ("CONFIGURATION", ()),
    "resource_exhaustion": (None, ("ASI02", "ASI08")),
    "code_execution": (None, ("ASI05",)),
    "missing_security_configuration": ("CONFIGURATION", ()),
    "arbitrary_file_read": (None, ("ASI02", "ASI03")),
    "arbitrary_command_execution": (None, ("ASI05", "ASI02")),
    "insecure_communication": (None, ("ASI07",)),
    "privacy_breach": (None, ("ASI03", "ASI02")),
    "unauthorized_action": (None, ("ASI02", "ASI03")),
    "dependency_confusion": (None, ("ASI04", "ASI05")),
    "arbitrary_script_execution": (None, ("ASI05", "ASI02")),
}

SNYK_CODE_MAP = {
    "W011": (None, ("ASI01", "ASI09")),
    "W012": (None, ("ASI04", "ASI05")),
    "E004": (None, ("ASI01",)),
    "W007": (None, ("ASI03", "ASI02")),
    "W013": (None, ("ASI02", "ASI05")),
    "E005": (None, ("ASI04", "ASI05")),
    "W009": (None, ("ASI03", "ASI02")),
    "E006": (None, ("ASI05", "ASI02")),
    "W021": (None, ("ASI01", "ASI09")),
}

SOCKET_CODE_MAP = {
    "gptAnomaly": (None, ("ASI04",)),
    "gptSecurity": (None, ("ASI04", "ASI05")),
    "gptMalware": (None, ("ASI04", "ASI05")),
    "obfuscatedFile": (None, ("ASI04", "ASI09")),
}

# AgentTrustHub: `code` è un insieme di token separati da virgola → unione ASI.
ATH_TOKEN_MAP = {
    "COMMAND_EXECUTION": ("ASI05", "ASI02"),
    "EXTERNAL_DOWNLOADS": ("ASI04", "ASI05"),
    "REMOTE_CODE_EXECUTION": ("ASI05", "ASI04"),
    "PROMPT_INJECTION": ("ASI01", "ASI09"),
    "PI_IGNORE_INSTRUCTIONS": ("ASI01",),
    "PI_CONCEALMENT": ("ASI09", "ASI01"),
    "PI_DAN_JAILBREAK": ("ASI01",),
    "PI_SYSTEM_PROMPT_EXTRACTION": ("ASI01", "ASI03"),
    "DATA_EXFILTRATION": ("ASI02", "ASI03"),
    "data_exfil_to_known_destination": ("ASI02", "ASI03"),
    "CREDENTIALS_UNSAFE": ("ASI03", "ASI02"),
    "hardcoded_api_keys": ("ASI03", "ASI02"),
    "hardcoded_connection_string": ("ASI03", "ASI02"),
    "AST_SUBPROCESS": ("ASI05", "ASI02"),
    "destructive_system_commands": ("ASI05", "ASI02"),
    "env_path_manipulation": ("ASI02", "ASI03"),
}

# Cisco SkillScanner: codici LLM_*/AST_* (il fallback keyword copre il resto).
CISCO_CODE_MAP = {
    "LLM_PROMPT_INJECTION": (None, ("ASI01", "ASI09")),
    "LLM_SUPPLY_CHAIN_ATTACK": (None, ("ASI04", "ASI05")),
    "LLM_SKILL_DISCOVERY_ABUSE": ("CONFIGURATION", ()),
    "LLM_DATA_EXFILTRATION": (None, ("ASI02", "ASI03")),
    "LLM_CREDENTIAL_THEFT": (None, ("ASI03", "ASI02")),
    "LLM_COMMAND_EXECUTION": (None, ("ASI05", "ASI02")),
    "LLM_PRIVILEGE_ESCALATION": (None, ("ASI03", "ASI02")),
}

ENGINE_CODE_MAPS = {
    "blue": BLUE_TYPE_MAP,
    "snyk": SNYK_CODE_MAP,
    "socket": SOCKET_CODE_MAP,
    "cisco": CISCO_CODE_MAP,
}

# Regole keyword (engine-agnostiche) quando codice/tipo non è nelle mappe.
KEYWORD_RULES = [
    (("allowed-tools", "allowed tools", "missing metadata", "referenced file", "packaging"), "CONFIGURATION", ()),
    (("prompt injection", "ignore previous", "ignore all previous", "goal hijack", "jailbreak"), None, ("ASI01", "ASI09")),
    (("exfiltrat", "data leak"), None, ("ASI02", "ASI03")),
    (("credential", "api key", "api-key", "password", "secret key"), None, ("ASI03", "ASI02")),
    (("privilege escalation", "over-privileged", "excessive permission", "unauthorized access"), None, ("ASI03", "ASI02")),
    (("remote script", "untrusted dependency", "unpinned", "supply chain", "third-party content"), None, ("ASI04", "ASI05")),
    (("arbitrary code execution", "command injection", "shell command", "code execution", "remote code execution"), None, ("ASI05", "ASI02")),
    (("memory poison", "context poison"), None, ("ASI06",)),
    (("inter-agent", "agent-to-agent", "trust boundary"), None, ("ASI07",)),
    (("cascading failure", "propagat"), None, ("ASI08",)),
    (("rogue agent", "outside its intended role"), None, ("ASI10",)),
]


def _js_json(obj) -> str:
    """JSON sicuro dentro un blocco <script>: ogni "<" diventa \\u003c.

    Scappare solo "</" non basta: un "<!--" seguito da "<script" nei contenuti
    (es. SKILL.md con esempi HTML) manda il tokenizer HTML in "script data
    double escaped state" e il </script> legittimo non chiude più il tag —
    i blocchi script si fondono e il JS muore con SyntaxError.
    """
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


def classify_finding(engine, code_or_type, title, description, quote):
    """(provenance_default, asi_default) per un finding.

    Provenance: CONFIGURATION quando codice/tipo/testo riguarda packaging o
    metadati; altrimenti PRE_EXISTING se c'è una citazione con cui confrontare
    il testo della skill; altrimenti AMBIGUOUS. INJECTED non è mai assegnata
    automaticamente (nessuna ground truth di injection nel modello per-motore),
    ma resta selezionabile a mano.
    """
    raw = f"{code_or_type or ''} {title or ''} {description or ''}".lower()
    # Codici come LLM_SUPPLY_CHAIN_ATTACK / PI_IGNORE_INSTRUCTIONS: normalizzare
    # _ e - a spazi li rende raggiungibili dalle regole keyword.
    text = re.sub(r"[_\-]+", " ", raw)
    prov_override, asi = None, ()

    cmap = ENGINE_CODE_MAPS.get(engine)
    if cmap and code_or_type in cmap:
        prov_override, asi = cmap[code_or_type]
    elif engine == "agentTrustHub" and code_or_type:
        found = set()
        for t in (t.strip() for t in code_or_type.split(",")):
            found.update(ATH_TOKEN_MAP.get(t, ()))
        if found:
            asi = tuple(sorted(found))
    if not asi and prov_override is None:
        for keywords, kw_prov, kw_asi in KEYWORD_RULES:
            if any(k in text for k in keywords):
                prov_override, asi = kw_prov, kw_asi
                break

    if prov_override:
        provenance = prov_override
    elif quote and len(quote.strip()) > 3:
        provenance = "PRE_EXISTING"
    else:
        provenance = "AMBIGUOUS"
    return provenance, list(asi)


# ── Lingua della skill (euristica su blocchi unicode, nessun modello) ────
LANG_BLOCKS = [
    ("Japanese", re.compile(r"[぀-ヿ]")),
    ("Chinese", re.compile(r"[一-鿿]")),
    ("Korean", re.compile(r"[가-힯]")),
    ("Russian", re.compile(r"[Ѐ-ӿ]")),
    ("Arabic", re.compile(r"[؀-ۿ]")),
    ("Hindi", re.compile(r"[ऀ-ॿ]")),
]
LANG_THRESHOLD = 20


def detect_language(text):
    text = text or ""
    for label, pattern in LANG_BLOCKS:
        if len(pattern.findall(text)) >= LANG_THRESHOLD:
            return label
    return "English / Latin script"


# ── Caricamento run + costruzione colonne ────────────────────────────────
def load_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    jf = run_dir / "results.json"
    if not jf.is_file():
        raise FileNotFoundError(f"{jf} non trovato")
    data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
    by_key = {}
    for rec in data.get("findings_detail") or []:
        k = case_key(rec)
        if k:
            by_key.setdefault(k, rec)
    return {"run_id": run_dir.name, "dir": run_dir, "data": data, "by_key": by_key}


def _short_names(run_ids: list[str]) -> dict[str, str]:
    """Suffisso distintivo di ogni run (prefisso comune rimosso), per etichette
    leggibili quando più run espongono lo stesso motore."""
    if len(run_ids) < 2:
        return {r: r for r in run_ids}
    prefix = run_ids[0]
    for r in run_ids[1:]:
        while prefix and not r.startswith(prefix):
            prefix = prefix[:-1]
    out = {}
    for r in run_ids:
        s = (r[len(prefix):].strip("_-") if prefix else r) or r
        # Run senza famiglia comune: il nome intero non sta in un'intestazione
        # di tabella — tengo gli ultimi due segmenti, che sono la parte
        # distintiva (…_Cisco_skill_scanner_noLLM → scanner_noLLM).
        if len(s) > 28:
            s = "_".join(s.split("_")[-2:])
        out[r] = s
    return out


def _engine_names(run: dict) -> list[str]:
    engs = [e for e in (run["data"].get("defense_engines") or []) if e]
    if engs:
        return engs
    seen = []
    for rec in run["by_key"].values():
        for e in (rec.get("engines") or {}):
            if e not in seen:
                seen.append(e)
    return seen


def _sub_engines(run: dict, eng: str) -> list[str]:
    """Sotto-motori esposti da un motore aggregatore (skills_sh → snyk/…)."""
    subs: list[str] = []
    for rec in run["by_key"].values():
        meta = ((rec.get("engines") or {}).get(eng) or {}).get("meta") or {}
        for s in (meta.get("sub_engines") or {}):
            if s not in subs:
                subs.append(s)
    return subs


def build_columns(runs: list[dict], ref: str | None = None) -> list[dict]:
    """Una colonna per (run, motore), con i motori aggregatori espansi nei loro
    sotto-motori. `ref` = "<run_id>:<engine>" oppure "<engine>"."""
    shorts = _short_names([r["run_id"] for r in runs])
    raw = []
    for run in runs:
        for eng in _engine_names(run):
            subs = _sub_engines(run, eng)
            if subs:
                for s in subs:
                    raw.append({"run": run, "engine": s, "parent": eng})
            else:
                raw.append({"run": run, "engine": eng, "parent": None})

    engine_counts = Counter(c["engine"] for c in raw)
    cols = []
    for c in raw:
        eng, run = c["engine"], c["run"]
        base_label = ENGINE_LABEL.get(eng, eng)
        if engine_counts[eng] > 1 and len(runs) > 1:
            label = f"{base_label} · {shorts[run['run_id']]}"
            key = f"{eng}@{run['run_id']}"
        else:
            label, key = base_label, eng
        cols.append({
            "key": re.sub(r"[^A-Za-z0-9_.@-]", "_", key),
            "label": label,
            "engine": eng,
            "parent": c["parent"],
            "run_id": run["run_id"],
            "_run": run,
        })

    # Colonna di riferimento: --ref esplicito, altrimenti la prima 'blue',
    # altrimenti la prima colonna.
    ref_idx = 0
    if ref:
        want_run, _, want_eng = ref.rpartition(":")
        for i, c in enumerate(cols):
            if c["engine"] == (want_eng or ref) and (not want_run or c["run_id"] == want_run):
                ref_idx = i
                break
    else:
        for i, c in enumerate(cols):
            if c["engine"] == "blue":
                ref_idx = i
                break
    cols.insert(0, cols.pop(ref_idx))
    for i, c in enumerate(cols):
        c["is_ref"] = (i == 0)
        c["color"] = "--s1" if i == 0 else OTHER_COLORS[(i - 1) % len(OTHER_COLORS)]
    return cols


def col_payload(col: dict, rec: dict) -> dict:
    """Blocco {flagged, findings, available, scan_error} della colonna per un caso."""
    engines = rec.get("engines") or {}
    if col["parent"]:
        parent = engines.get(col["parent"]) or {}
        blk = ((parent.get("meta") or {}).get("sub_engines") or {}).get(col["engine"]) or {}
        # Disponibilità/errore ereditati dal motore aggregatore.
        blk = dict(blk)
        blk.setdefault("available", parent.get("available", True))
        blk.setdefault("scan_error", parent.get("scan_error"))
        return blk
    return engines.get(col["engine"]) or {}


# ── Modello dati ─────────────────────────────────────────────────────────
def build_model(run_dirs, ref: str | None = None, title: str | None = None) -> dict:
    runs = [load_run(Path(d)) for d in run_dirs]
    cols = build_columns(runs, ref=ref)
    ref_col, other_cols = cols[0], cols[1:]

    # Casi presenti in TUTTE le run (le altre non sono confrontabili).
    key_sets = [set(r["by_key"]) for r in runs]
    common = set.intersection(*key_sets) if key_sets else set()
    only_some = set.union(*key_sets) - common if key_sets else set()

    # Ordine stabile: quello della prima run.
    ordered = [k for k in runs[0]["by_key"] if k in common]

    excluded_unavailable = 0
    excluded_scan_error = 0
    rows = []
    for k in ordered:
        recs = {c["key"]: c["_run"]["by_key"][k] for c in cols}
        blocks = {c["key"]: col_payload(c, recs[c["key"]]) for c in cols}
        if any(b.get("available") is False for b in blocks.values()):
            excluded_unavailable += 1
            continue
        if any(b.get("scan_error") for b in blocks.values()):
            excluded_scan_error += 1
            continue
        rows.append({"key": k, "recs": recs, "blocks": blocks})

    N = len(rows)
    ref_key = ref_col["key"]

    def flagged(row, ckey):
        return bool(row["blocks"][ckey].get("flagged"))

    def findings(row, ckey):
        return row["blocks"][ckey].get("findings") or []

    def any_others(row):
        return any(flagged(row, c["key"]) for c in other_cols)

    # ── Overview ────────────────────────────────────────────────────────
    has_agg = len(other_cols) > 1
    agg_label = f"Any other scanner ({len(other_cols)})"
    overview = [{"engine": ref_key, "label": ref_col["label"],
                 "flagged": sum(1 for r in rows if flagged(r, ref_key)), "color": "--s1"}]
    if has_agg:
        overview.append({"engine": "__any__", "label": agg_label,
                         "flagged": sum(1 for r in rows if any_others(r)), "color": "--s2"})
    for c in other_cols:
        overview.append({"engine": c["key"], "label": c["label"],
                         "flagged": sum(1 for r in rows if flagged(r, c["key"])), "color": c["color"]})
    for o in overview:
        o["total"] = N
        o["rate"] = round(o["flagged"] / N * 100, 1) if N else 0.0

    # ── Agreement ───────────────────────────────────────────────────────
    ref_flag = sum(1 for r in rows if flagged(r, ref_key))
    any_flag = sum(1 for r in rows if any_others(r))
    both = sum(1 for r in rows if flagged(r, ref_key) and any_others(r))
    agreement = {"both": both, "ref_only": ref_flag - both,
                 "others_only": any_flag - both,
                 "neither": N - both - (ref_flag - both) - (any_flag - both)}

    per_col_agreement = {}
    for c in other_cols:
        b = sum(1 for r in rows if flagged(r, ref_key) and flagged(r, c["key"]))
        eo = sum(1 for r in rows if flagged(r, c["key"])) - b
        per_col_agreement[c["key"]] = {
            "both": b, "ref_only": ref_flag - b, "engine_only": eo,
            "neither": N - b - (ref_flag - b) - eo,
        }

    # ── Severity / codici ───────────────────────────────────────────────
    severity_dist, top_codes = {}, {}
    for c in cols:
        sev = Counter()
        codes = Counter()
        titles = {}
        for r in rows:
            for f in findings(r, c["key"]):
                sev[(f.get("severity") or "").lower()] += 1
                code = f.get("code") or f.get("type") or "?"
                codes[code] += 1
                titles.setdefault(code, (f.get("title") or f.get("type") or "")[:90])
        severity_dist[c["key"]] = dict(sev)
        top_codes[c["key"]] = [{"code": k, "count": v, "title": titles.get(k, "")}
                               for k, v in codes.most_common(15)]

    # ── Categoria (tag proprio del motore di riferimento) ───────────────
    def ref_categories(row):
        rec = row["recs"][ref_key]
        cats = rec.get("blue_categories")
        if cats:
            return cats
        vt = rec.get("vuln_type")
        return [vt] if vt else ["?"]

    by_category = defaultdict(lambda: {"total": 0, "ref": 0, "others": 0, "both": 0})
    for r in rows:
        is_ref, is_oth = flagged(r, ref_key), any_others(r)
        for cat in ref_categories(r):
            d = by_category[cat]
            d["total"] += 1
            if is_ref: d["ref"] += 1
            if is_oth: d["others"] += 1
            if is_ref and is_oth: d["both"] += 1
    if "user_provided" in by_category:
        by_category[f"no {ref_col['label']} finding (miss)"] = by_category.pop("user_provided")
    by_category = dict(sorted(by_category.items(), key=lambda kv: -kv[1]["total"]))

    # ── Tier di popolarità (solo se i rank variano davvero) ─────────────
    def rank_of(row):
        try:
            return int(row["recs"][ref_key].get("popularity_rank") or 0)
        except (TypeError, ValueError):
            return 0

    ranks = {rank_of(r) for r in rows}
    by_tier = []
    if len(ranks) > 1:
        for label, lo, hi in [("Top 100", 0, 100), ("101-300", 100, 300),
                              ("301-600", 300, 600), ("601+", 600, 10_000_000)]:
            trows = [r for r in rows if lo <= rank_of(r) < hi]
            t = len(trows)
            if not t:
                continue
            by_tier.append({
                "label": label, "total": t, "lo": lo, "hi": hi,
                "ref_rate": round(sum(1 for r in trows if flagged(r, ref_key)) / t * 100, 1),
                "others_rate": round(sum(1 for r in trows if any_others(r)) / t * 100, 1),
            })

    # ── Contenuto della skill (per lingua / sezione SKILL.md) ───────────
    def skill_content(row):
        for c in cols:
            rec = row["recs"][c["key"]]
            txt = rec.get("skill_content_injected")
            if txt:
                return txt
        path = row["recs"][ref_key].get("inj_path")
        if path:
            p = Path(path)
            if p.is_file():
                try:
                    return p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    pass
        return ""

    contents = {r["key"]: skill_content(r) for r in rows}

    def skill_name(row):
        return row["recs"][ref_key].get("skill") or row["key"]

    # ── Leaderboard org / lingua ────────────────────────────────────────
    def leaderboard(bucket_fn):
        acc = defaultdict(lambda: {"total": 0, "ref_flagged": 0, "ref_findings": 0,
                                    "others_flagged": 0, "others_findings": 0})
        for r in rows:
            d = acc[bucket_fn(r)]
            d["total"] += 1
            if flagged(r, ref_key):
                d["ref_flagged"] += 1
            d["ref_findings"] += len(findings(r, ref_key))
            if any_others(r):
                d["others_flagged"] += 1
            for c in other_cols:
                d["others_findings"] += len(findings(r, c["key"]))
        for d in acc.values():
            d["total_findings"] = d["ref_findings"] + d["others_findings"]
        out = [{"name": k, **v} for k, v in acc.items()]
        out.sort(key=lambda d: (-d["total_findings"], -d["total"]))
        return out

    by_org = leaderboard(lambda r: (skill_name(r) or "?").split("__")[0])
    show_orgs = len(by_org) > 1 and any("__" in (skill_name(r) or "") for r in rows)
    by_lang = leaderboard(lambda r: detect_language(contents[r["key"]]))

    # ── Righe per l'explorer ────────────────────────────────────────────
    def bucket(r):
        b, s = flagged(r, ref_key), any_others(r)
        if b and s: return "both"
        if b: return "ref_only"
        if s: return "others_only"
        return "neither"

    skill_rows = []
    for r in rows:
        name = skill_name(r)
        cols_out = {}
        for c in cols:
            out = []
            for i, f in enumerate(findings(r, c["key"])):
                code = f.get("code") or f.get("type")
                prov, asi = classify_finding(c["engine"], code, f.get("title") or f.get("type"),
                                             f.get("description"), f.get("quote"))
                out.append({
                    "id": f"{r['key']}::{c['key']}::{i}",
                    "code": f.get("code"), "type": f.get("type"),
                    "severity": f.get("severity"),
                    "title": f.get("title") or f.get("type"),
                    "description": f.get("description"), "quote": f.get("quote"),
                    "provenance": prov, "asi": asi,
                    "verdict": "unreviewed", "note": "",
                })
            fs = findings(r, c["key"])
            cols_out[c["key"]] = {
                "flagged": flagged(r, c["key"]),
                "top_code": (fs[0].get("code") or fs[0].get("type")) if fs else None,
                "top_sev": fs[0].get("severity") if fs else None,
                "findings": out,
            }

        ref_rec = r["recs"][ref_key]
        skill_rows.append({
            "skill": name,
            "key": r["key"],
            "rank": ref_rec.get("popularity_rank"),
            "lang": detect_language(contents[r["key"]]),
            "skill_content": contents[r["key"]],
            "categories": ref_categories(r),
            "cols": cols_out,
            "any_others": any_others(r),
            "bucket": bucket(r),
            "patch_reasoning": ref_rec.get("patch_reasoning") or None,
            "patches_applied": [{"original": p.get("original"), "replacement": p.get("replacement")}
                                for p in (ref_rec.get("patches_applied") or [])],
        })

    meta_runs = [{
        "run_id": r["run_id"],
        "started_at": r["data"].get("started_at"),
        "ended_at": r["data"].get("ended_at"),
        "model": r["data"].get("model"),
        "total": r["data"].get("total"),
        "engines": _engine_names(r),
    } for r in runs]

    return {
        "title": title or _default_title(cols, runs),
        "n": N,
        "columns": [{k: v for k, v in c.items() if k != "_run"} for c in cols],
        "ref": ref_key,
        "ref_label": ref_col["label"],
        "agg_label": agg_label,
        "has_agg": has_agg,
        "overview": overview,
        "agreement": agreement,
        "per_col_agreement": per_col_agreement,
        "severity_dist": severity_dist,
        "top_codes": top_codes,
        "by_category": by_category,
        "by_tier": by_tier,
        "by_org": by_org if show_orgs else [],
        "by_lang": by_lang,
        "skills": skill_rows,
        "provenance_labels": PROVENANCE_LABELS,
        "asi_labels": ASI_LABELS,
        "meta": {
            "runs": meta_runs,
            "cases_common": len(common),
            "cases_partial": len(only_some),
            "excluded_unavailable": excluded_unavailable,
            "excluded_scan_error": excluded_scan_error,
        },
    }


def _default_title(cols, runs):
    head, others = cols[0]["label"], cols[1:]
    if not others:
        return f"{head} — {len(runs)} run"
    if len(others) <= 2:
        return f"{head} vs {', '.join(c['label'] for c in others)}"
    return f"{head} vs {len(others)} other engines ({len(runs)} runs)"


# ═════════════════════════════════════════════════════════════════════════
# HTML rendering
# ═════════════════════════════════════════════════════════════════════════
SEV_STATUS = {"low": "good", "clean": "good", "medium": "warning", "middle": "warning",
              "high": "serious", "critical": "critical"}


def sev_pill(sev):
    if not sev:
        return '<span class="pill pill-muted">&mdash;</span>'
    status = SEV_STATUS.get(sev.lower(), "warning")
    return f'<span class="pill pill-{status}">{sev}</span>'


def bar_row(label, value, total, color_var, note=""):
    pct = round(value / total * 100, 1) if total else 0.0
    return f'''
    <div class="bar-row">
      <div class="bar-label">{label}{f' <span class="bar-note">{note}</span>' if note else ''}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{pct}%;background:var({color_var})"></div>
      </div>
      <div class="bar-value">{value} <span class="bar-pct">({pct}%)</span></div>
    </div>'''


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_html(m: dict, storage_id: str) -> str:
    N = m["n"]
    cols = m["columns"]
    ref_label = m["ref_label"]
    agg_label = m["agg_label"]
    other_cols = [c for c in cols if not c["is_ref"]]
    others_label = agg_label if m["has_agg"] else (other_cols[0]["label"] if other_cols else "—")

    overview_bars = "".join(bar_row(o["label"], o["flagged"], N, o["color"]) for o in m["overview"])

    agreement_labels = {"both": "Both flagged", "ref_only": f"{ref_label} only",
                        "others_only": f"{others_label} only", "neither": "Neither"}
    agreement_colors = {"both": "--s1", "ref_only": "--s2", "others_only": "--s3", "neither": "--muted"}
    agreement_bars = "".join(bar_row(agreement_labels[k], v, N, agreement_colors[k])
                             for k, v in m["agreement"].items())

    per_col_html = ""
    for c in other_cols:
        a = m["per_col_agreement"][c["key"]]
        per_col_html += f'''
    <div class="mini-agreement">
      <h4>{_esc(ref_label)} vs {_esc(c["label"])}</h4>
      {bar_row("Both", a["both"], N, "--s1")}
      {bar_row(f"{_esc(ref_label)} only", a["ref_only"], N, "--s2")}
      {bar_row(f"{_esc(c['label'])} only", a["engine_only"], N, "--s3")}
      {bar_row("Neither", a["neither"], N, "--muted")}
    </div>'''

    # Severità
    sev_order = ["low", "clean", "medium", "middle", "high", "critical"]
    all_sevs = []
    for c in cols:
        for s in m["severity_dist"][c["key"]]:
            if s and s not in all_sevs:
                all_sevs.append(s)
    all_sevs.sort(key=lambda s: sev_order.index(s) if s in sev_order else 99)
    sev_table_header = "".join(f"<th>{sev_pill(s)}</th>" for s in all_sevs)
    sev_table_rows = ""
    for c in cols:
        cells = "".join(f"<td>{m['severity_dist'][c['key']].get(s, 0) or '&mdash;'}</td>" for s in all_sevs)
        sev_table_rows += f"<tr><td class='rowhead'>{_esc(c['label'])}</td>{cells}</tr>"

    # Codici
    def codes_table(c):
        trs = "".join(
            f"<tr class='clickable-row' data-engine='{_esc(c['key'])}' data-code='{_esc(x['code'])}'>"
            f"<td class='mono'>{_esc(x['code'])}</td><td>{x['count']}</td>"
            f"<td class='muted-text'>{_esc(x['title'])}</td></tr>"
            for x in m["top_codes"][c["key"]]
        )
        return f'''
    <div class="codes-col">
      <h4>{_esc(c["label"])}</h4>
      <table class="data-table small" id="codesTable-{_esc(c['key'])}">
        <thead><tr><th>Code</th><th>#</th><th>Title</th></tr></thead>
        <tbody>{trs or "<tr><td colspan='3' class='muted-text'>&mdash;</td></tr>"}</tbody>
      </table>
    </div>'''

    codes_html = "".join(codes_table(c) for c in cols)

    cat_rows_html = ""
    for cat, d in m["by_category"].items():
        t = d["total"]
        b_pct = round(d["ref"] / t * 100, 1) if t else 0
        s_pct = round(d["others"] / t * 100, 1) if t else 0
        cat_rows_html += f'''
    <tr class="clickable-row" data-cat="{_esc(cat)}">
      <td>{_esc(cat)}</td>
      <td class="num">{t}</td>
      <td class="num">{d["ref"]}</td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:{b_pct}%;background:var(--s1)"></div></div>
        <span class="inline-val">{b_pct}%</span>
      </td>
      <td class="num">{d["others"]}</td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:{s_pct}%;background:var(--s2)"></div></div>
        <span class="inline-val">{s_pct}%</span>
      </td>
      <td class="num">{d["both"]}</td>
    </tr>'''

    tier_rows_html = ""
    for t in m["by_tier"]:
        tier_rows_html += f'''
    <tr class="clickable-row" data-lo="{t["lo"]}" data-hi="{t["hi"]}">
      <td>{t["label"]}</td>
      <td class="num">{t["total"]}</td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:{t["ref_rate"]}%;background:var(--s1)"></div></div>
        <span class="inline-val">{t["ref_rate"]}%</span>
      </td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:{t["others_rate"]}%;background:var(--s2)"></div></div>
        <span class="inline-val">{t["others_rate"]}%</span>
      </td>
    </tr>'''

    def leaderboard_rows(items, attr):
        html = ""
        for o in items:
            r_rate = round(o["ref_flagged"] / o["total"] * 100, 1) if o["total"] else 0
            o_rate = round(o["others_flagged"] / o["total"] * 100, 1) if o["total"] else 0
            html += f'''
    <tr class="clickable-row" data-{attr}="{_esc(o["name"])}">
      <td>{_esc(o["name"])}</td>
      <td class="num">{o["total"]}</td>
      <td class="num">{o["ref_flagged"]}</td>
      <td class="num">{r_rate}%</td>
      <td class="num">{o["others_flagged"]}</td>
      <td class="num">{o_rate}%</td>
      <td class="num">{o["ref_findings"]}</td>
      <td class="num">{o["others_findings"]}</td>
      <td class="num"><strong>{o["total_findings"]}</strong></td>
    </tr>'''
        return html

    org_rows_html = leaderboard_rows(m["by_org"], "org")
    lang_rows_html = leaderboard_rows(m["by_lang"], "lang")

    DATA_JSON = _js_json(m["skills"])
    COLS_JSON = _js_json([{k: c[k] for k in ("key", "label", "color", "engine", "run_id", "is_ref")}
                          for c in cols])

    runs_line = " &middot; ".join(
        f"{_esc(r['run_id'])} ({', '.join(r['engines'])})" for r in m["meta"]["runs"])
    excl = m["meta"]
    excl_note = (f"{excl['cases_partial']} not present in all runs, "
                 f"{excl['excluded_unavailable']} with an unavailable engine, "
                 f"{excl['excluded_scan_error']} with a scan error")

    n_cols = len(cols)
    detail_colspan = 4 + n_cols

    col_headers = "".join(
        f'<th data-key="{_esc(c["key"])}">{_esc(c["label"])}</th>' for c in cols)
    engine_chips = "".join(
        f'<span class="chip" data-filter="eng::{_esc(c["key"])}">{_esc(c["label"])} flagged</span>'
        for c in cols)

    tier_section = f'''
  <h2 id="sec-tier">Flag rate by popularity tier</h2>
  <div class="card">
    <div class="legend">
      <span><span class="legend-dot" style="background:var(--s1)"></span>{_esc(ref_label)}</span>
      <span><span class="legend-dot" style="background:var(--s2)"></span>{_esc(others_label)}</span>
    </div>
    <table class="data-table" id="tierTable">
      <thead><tr><th>Popularity rank</th><th class="num">N</th><th>{_esc(ref_label)} rate</th><th>{_esc(others_label)} rate</th></tr></thead>
      <tbody>{tier_rows_html}</tbody>
    </table>
    <p class="count-note">Rank 0 = most installed skill (skills.sh dataset).</p>
  </div>''' if m["by_tier"] else ""

    org_section = f'''
  <h2 id="sec-orgs">Vulnerabilities by skill author/org</h2>
  <div class="card">
    <p class="count-note">Org = first segment of the skill id (<code>org__repo__skill</code>). Sorted by total findings.</p>
    <div class="table-scroll" style="max-height:480px">
      <table class="data-table" id="orgTable">
        <thead><tr><th>Org</th><th class="num">Skills</th><th class="num">{_esc(ref_label)} flagged #</th><th class="num">{_esc(ref_label)} flagged %</th><th class="num">{_esc(others_label)} flagged #</th><th class="num">{_esc(others_label)} flagged %</th><th class="num">{_esc(ref_label)} findings</th><th class="num">{_esc(others_label)} findings</th><th class="num">Total findings</th></tr></thead>
        <tbody>{org_rows_html}</tbody>
      </table>
    </div>
  </div>''' if m["by_org"] else ""

    toc_tier = '<a href="#sec-tier">Popularity</a>' if m["by_tier"] else ""
    toc_orgs = '<a href="#sec-orgs">Orgs</a>' if m["by_org"] else ""

    return f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(m["title"])}</title>
<style>
.viz-root {{
  color-scheme: light;
  --surface-1: #fcfcfb; --page: #f9f9f7;
  --text-primary: #0b0b0b; --text-secondary: #52514e; --muted: #898781;
  --grid: #e1e0d9; --baseline: #c3c2b7; --border: rgba(11,11,11,0.10);
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100; --s5: #e87ba4;
  --s6: #8a63d2; --s7: #00a0b0; --s8: #b5651d; --s9: #6b8e23; --s10: #c2185b;
  --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
}}
:root[data-theme="dark"] .viz-root {{
  color-scheme: dark;
  --surface-1: #1a1a19; --page: #0d0d0d;
  --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181;
  --s6: #9b7ae0; --s7: #17b3c4; --s8: #c9782f; --s9: #7ba233; --s10: #d8447a;
  --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); }}
.viz-root {{
  background: var(--page); color: var(--text-primary); min-height: 100vh;
  font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 14px; line-height: 1.5;
}}
.wrap {{ max-width: 1400px; margin: 0 auto; padding: 28px 22px 64px; }}
.top-row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }}
h1 {{ font-size: 24px; font-weight: 650; margin: 0 0 4px; letter-spacing: -0.01em; }}
h2 {{ font-size: 17px; font-weight: 620; margin: 34px 0 12px; letter-spacing: -0.01em; }}
h3 {{ font-size: 14px; font-weight: 600; margin: 0 0 10px; }}
h4 {{ font-size: 12.5px; font-weight: 600; margin: 0 0 8px; color: var(--text-secondary); }}
.subtitle {{ color: var(--text-secondary); margin: 0 0 2px; font-size: 13px; }}
.meta-line {{ color: var(--muted); margin: 0; font-size: 12px; }}
.theme-toggle {{
  background: var(--surface-1); border: 1px solid var(--border); color: var(--text-secondary);
  border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; white-space: nowrap;
}}
.toc {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 16px 0 4px; }}
.toc a {{
  font-size: 11.5px; color: var(--text-secondary); text-decoration: none;
  border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px; background: var(--surface-1);
}}
.toc a:hover {{ color: var(--text-primary); border-color: var(--baseline); }}
.caveat {{
  margin-top: 14px; padding: 10px 14px; border-left: 3px solid var(--s2);
  background: var(--surface-1); border-radius: 0 8px 8px 0; font-size: 12.5px; color: var(--text-secondary);
}}
.card {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
@media (max-width: 1000px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
.kpi-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }}
.kpi {{
  flex: 1 1 150px; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 14px; border-top: 3px solid var(--baseline);
}}
.kpi .val {{ font-size: 22px; font-weight: 650; }}
.kpi .lbl {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 2px; }}
.bar-row {{ display: flex; align-items: center; gap: 12px; margin: 7px 0; }}
.bar-label {{ width: 220px; font-size: 12.5px; color: var(--text-secondary); flex-shrink: 0; }}
.bar-note {{ color: var(--muted); font-size: 11px; }}
.bar-track {{ flex: 1; height: 16px; background: var(--grid); border-radius: 4px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 4px; }}
.bar-value {{ width: 96px; text-align: right; font-size: 12.5px; font-variant-numeric: tabular-nums; }}
.bar-pct {{ color: var(--muted); font-size: 11.5px; }}
.mini-row-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }}
.mini-agreement .bar-label {{ width: 120px; font-size: 11.5px; }}
.mini-agreement .bar-value {{ width: 74px; font-size: 11.5px; }}
.data-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
.data-table th {{
  text-align: left; font-weight: 600; color: var(--text-secondary); padding: 7px 10px;
  border-bottom: 1px solid var(--baseline); white-space: nowrap; position: sticky; top: 0; background: var(--surface-1);
}}
.data-table td {{ padding: 6px 10px; border-bottom: 1px solid var(--grid); vertical-align: middle; }}
.data-table td.num, .data-table th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.data-table td.rowhead {{ font-weight: 600; }}
.data-table.small td, .data-table.small th {{ padding: 4px 8px; font-size: 11.5px; }}
.table-scroll {{ overflow: auto; }}
.table-flow {{ overflow-x: auto; }}
.sortable-th {{ cursor: pointer; user-select: none; }}
.sortable-th:hover {{ color: var(--text-primary); }}
.sort-arrow {{ font-size: 9px; margin-left: 4px; color: var(--muted); }}
th.sort-active {{ color: var(--text-primary); }}
.clickable-row {{ cursor: pointer; }}
.clickable-row:hover {{ background: var(--page); }}
.pill {{ display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 600; }}
.pill-good {{ background: color-mix(in srgb, var(--good) 18%, transparent); color: var(--good); }}
.pill-warning {{ background: color-mix(in srgb, var(--warning) 22%, transparent); color: #8a6100; }}
.pill-serious {{ background: color-mix(in srgb, var(--serious) 22%, transparent); color: #a24a20; }}
.pill-critical {{ background: color-mix(in srgb, var(--critical) 18%, transparent); color: var(--critical); }}
.pill-muted {{ background: var(--grid); color: var(--muted); }}
.pill-flag-yes {{ background: color-mix(in srgb, var(--critical) 16%, transparent); color: var(--critical); }}
.pill-flag-no {{ background: var(--grid); color: var(--muted); }}
:root[data-theme="dark"] .pill-warning {{ color: #f0c04a; }}
:root[data-theme="dark"] .pill-serious {{ color: #f0a179; }}
.inline-bar {{ display: inline-block; width: 90px; height: 8px; background: var(--grid); border-radius: 3px; overflow: hidden; vertical-align: middle; }}
.inline-fill {{ height: 100%; }}
.inline-val {{ font-size: 11.5px; color: var(--text-secondary); margin-left: 6px; font-variant-numeric: tabular-nums; }}
.legend {{ display: flex; gap: 16px; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 10px; }}
.legend-dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 5px; }}
.codes-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }}
.count-note {{ font-size: 11.5px; color: var(--muted); margin: 10px 0 0; }}
.filter-badge {{ font-size: 11.5px; color: var(--s2); margin: 6px 0 0; }}
.filters {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }}
.filters input[type=text] {{
  background: var(--page); border: 1px solid var(--border); color: var(--text-primary);
  border-radius: 6px; padding: 6px 10px; font-size: 12.5px; min-width: 220px;
}}
.filter-select {{
  background: var(--page); border: 1px solid var(--border); color: var(--text-primary);
  border-radius: 6px; padding: 6px 8px; font-size: 12px;
}}
.chip {{
  font-size: 11.5px; padding: 4px 10px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--border); color: var(--text-secondary); background: var(--page); user-select: none;
}}
.chip.active {{ background: var(--s1); border-color: var(--s1); color: #fff; }}
.toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }}
.toolbar-btn {{
  font-size: 11.5px; padding: 5px 11px; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--border); color: var(--text-secondary); background: var(--page); user-select: none;
}}
.toolbar-btn.primary {{ background: var(--s1); border-color: var(--s1); color: #fff; }}
.toolbar-note {{ font-size: 11px; color: var(--muted); }}
.taxo-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
.taxo-card {{ border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: var(--page); }}
.taxo-metric {{ display: flex; justify-content: space-between; font-size: 12px; padding: 2px 0; }}
.taxo-metric .k {{ color: var(--text-secondary); }}
.taxo-metric .v {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
.taxo-sub {{ margin-top: 10px; }}
.taxo-sub-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); margin: 8px 0 4px; }}
.taxo-dist-row {{ display: flex; align-items: center; gap: 8px; margin: 3px 0; }}
.taxo-dist-label {{ width: 120px; font-size: 11px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.taxo-dist-track {{ flex: 1; height: 8px; background: var(--grid); border-radius: 3px; overflow: hidden; }}
.taxo-dist-fill {{ height: 100%; }}
.taxo-dist-val {{ width: 34px; text-align: right; font-size: 11px; font-variant-numeric: tabular-nums; color: var(--text-secondary); }}
.row-main td {{ cursor: pointer; }}
.row-main:hover td {{ background: var(--page); }}
.chevron {{ color: var(--muted); width: 22px; }}
.row-detail td {{ background: var(--page); padding: 0; }}
.detail-panel {{ padding: 12px 16px 16px; }}
.detail-section {{ border-left: 3px solid var(--baseline); padding-left: 12px; margin: 10px 0; }}
.detail-section > summary {{ cursor: pointer; font-size: 12px; font-weight: 600; color: var(--text-secondary); }}
.detail-section-body {{ margin-top: 8px; }}
.finding-item {{ margin: 8px 0 12px; font-size: 12.5px; }}
.finding-item p {{ margin: 4px 0; color: var(--text-secondary); }}
.finding-item blockquote {{
  margin: 6px 0; padding: 6px 10px; border-left: 2px solid var(--grid); background: var(--surface-1);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px;
  white-space: pre-wrap; word-break: break-word; max-height: 220px; overflow: auto;
}}
.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
.muted-text {{ color: var(--muted); }}
.skillmd-pre {{
  margin: 0; padding: 10px 12px; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11.5px; white-space: pre-wrap; word-break: break-word; max-height: 460px; overflow: auto;
}}
.patch-item {{ margin: 8px 0 14px; font-size: 12px; }}
.patch-num {{ font-size: 11px; color: var(--muted); margin-bottom: 4px; }}
.patch-reasoning {{ font-style: italic; margin: 0 0 8px; white-space: pre-wrap; }}
.diff-removed, .diff-added {{ border-radius: 6px; padding: 6px 10px; margin: 4px 0; }}
.diff-removed {{ background: color-mix(in srgb, var(--critical) 8%, var(--surface-1)); }}
.diff-added {{ background: color-mix(in srgb, var(--good) 8%, var(--surface-1)); }}
.diff-label {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); margin-bottom: 3px; }}
.diff-removed pre, .diff-added pre {{
  margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px;
  white-space: pre-wrap; word-break: break-word;
}}
footer {{ margin-top: 40px; font-size: 11px; color: var(--muted); }}
.finding-editor {{ margin-top: 8px; padding: 8px 10px; background: var(--surface-1); border: 1px solid var(--border); border-radius: 6px; }}
.editor-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 4px 0; }}
.editor-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); width: 84px; flex-shrink: 0; }}
.prov-select {{ background: var(--page); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; padding: 4px 8px; font-size: 12px; }}
.verdict-group {{ display: flex; gap: 6px; }}
.verdict-btn {{
  font-size: 11.5px; padding: 3px 10px; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--border); color: var(--text-secondary); background: var(--page); user-select: none;
}}
.verdict-btn.active.confirmed {{ background: var(--good); border-color: var(--good); color: #fff; }}
.verdict-btn.active.disputed {{ background: var(--critical); border-color: var(--critical); color: #fff; }}
.asi-check-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px 14px; flex: 1; min-width: 280px; }}
.asi-check {{ display: flex; align-items: center; gap: 6px; font-size: 11.5px; cursor: pointer; color: var(--text-secondary); }}
.asi-check input {{ accent-color: var(--s1); cursor: pointer; }}
.asi-check.active {{ color: var(--text-primary); font-weight: 600; }}
.note-input {{
  flex: 1; min-width: 240px; background: var(--page); border: 1px solid var(--border); color: var(--text-primary);
  border-radius: 6px; padding: 6px 8px; font-size: 12px; font-family: inherit; resize: vertical; min-height: 34px;
}}
.finding-item.verdict-confirmed {{ border-left: 3px solid var(--good); padding-left: 9px; }}
.finding-item.verdict-disputed {{ border-left: 3px solid var(--critical); padding-left: 9px; }}
</style>
</head>
<body>
<div class="viz-root">
<div class="wrap">

  <div class="top-row">
    <div>
      <h1>{_esc(m["title"])}</h1>
      <p class="subtitle">{len(m["meta"]["runs"])} runs on the same dataset &mdash; N compared = {N} cases</p>
      <p class="meta-line">{runs_line}</p>
    </div>
    <button class="theme-toggle" onclick="toggleTheme()">Toggle dark mode</button>
  </div>

  <nav class="toc">
    <a href="#sec-overview">Overview</a>
    <a href="#sec-taxonomy">Taxonomy</a>
    <a href="#sec-agreement">Agreement</a>
    <a href="#sec-severity">Severity</a>
    <a href="#sec-codes">Rule codes</a>
    <a href="#sec-category">Category</a>
    <a href="#sec-asi">ASI class</a>
    <a href="#sec-provenance">Provenance</a>
    {toc_tier}
    {toc_orgs}
    <a href="#sec-lang">Language</a>
    <a href="#sec-explorer">Explorer</a>
  </nav>

  <div class="caveat">
    <strong>How to read this report.</strong> Columns are (run, engine): every engine scanned
    the same input files. Reference = <strong>{_esc(ref_label)}</strong>; "{_esc(others_label)}" =
    flagged by at least one of the other engines. Excluded from the comparison: {excl_note} &mdash; N={N}.
    <strong>Sorting:</strong> click a header to sort (shift+click adds a secondary key).
  </div>

  <h2 id="sec-overview">Overview &mdash; flag rate by engine</h2>
  <div class="kpi-row">
    {"".join(f'<div class="kpi" style="border-top-color:var({o["color"]})"><div class="val">{o["rate"]}%</div><div class="lbl">{_esc(o["label"])}<br>{o["flagged"]}/{N}</div></div>' for o in m["overview"])}
  </div>
  <div class="card">
    {overview_bars}
  </div>

  <h2 id="sec-taxonomy">Finding taxonomy &mdash; by engine (editable)</h2>
  <div class="card">
    <div class="toolbar">
      <span class="toolbar-btn primary" id="saveReportBtn">Save report (bake edits into this .html)</span>
      <span class="toolbar-btn" id="resetClassBtn">Reset all classifications</span>
      <span class="toolbar-note">Provenance &amp; ASI class are editable per finding (Per-skill explorer). Edits are saved in this browser; "Save report" writes them to the file.</span>
    </div>
    <div class="taxo-grid" id="taxoGrid"></div>
    <p class="count-note">Provenance/ASI defaults are auto-classified from each engine's code/type + text (see Finding_Taxonomy.md); INJECTED is never assigned automatically but remains selectable. "Scan failures" = cases with no finding at all out of N={N}.</p>
  </div>

  <h2 id="sec-agreement">Agreement &mdash; {_esc(ref_label)} vs {_esc(others_label)}</h2>
  <div class="grid-2">
    <div class="card">
      <h3>Overlap breakdown (% of N={N})</h3>
      {agreement_bars}
      <p class="count-note">"Both" = the reference and at least one other engine flagged the same case. "Neither" = clean across all engines.</p>
    </div>
    <div class="card">
      <h3>Agreement with {_esc(ref_label)}, by engine</h3>
      <div class="mini-row-3">
        {per_col_html}
      </div>
    </div>
  </div>

  <h2 id="sec-severity">Severity distribution (raw findings, each engine's own vocabulary)</h2>
  <div class="card">
    <div class="table-scroll" style="max-height:none">
      <table class="data-table" id="sevTable">
        <thead><tr><th>Engine</th>{sev_table_header}</tr></thead>
        <tbody>{sev_table_rows}</tbody>
      </table>
    </div>
    <p class="count-note">The severity vocabulary differs from engine to engine &mdash; shown as-is, colored by equivalent status.</p>
  </div>

  <h2 id="sec-codes">Top rule codes by engine</h2>
  <div class="card">
    <div class="codes-row">
      {codes_html}
    </div>
  </div>

  <h2 id="sec-category">Detection rate by vulnerability category</h2>
  <div class="card">
    <div class="legend">
      <span><span class="legend-dot" style="background:var(--s1)"></span>{_esc(ref_label)}</span>
      <span><span class="legend-dot" style="background:var(--s2)"></span>{_esc(others_label)}</span>
    </div>
    <div class="table-scroll" style="max-height:480px">
      <table class="data-table" id="categoryTable">
        <thead><tr><th>Category</th><th class="num">N</th><th class="num">{_esc(ref_label)} #</th><th>%</th><th class="num">{_esc(others_label)} #</th><th>%</th><th class="num">Both</th></tr></thead>
        <tbody>{cat_rows_html}</tbody>
      </table>
    </div>
    <p class="count-note">Category = the reference engine's own tag per case (fixed, not editable).</p>
  </div>

  <h2 id="sec-asi">Detection rate by ASI class (taxonomy, editable)</h2>
  <div class="card">
    <div class="legend">
      <span><span class="legend-dot" style="background:var(--s1)"></span>{_esc(ref_label)}</span>
      <span><span class="legend-dot" style="background:var(--s2)"></span>{_esc(others_label)}</span>
    </div>
    <div class="table-scroll" style="max-height:480px">
      <table class="data-table" id="asiCatTable">
        <thead><tr><th>ASI class</th><th class="num">N (union)</th><th class="num">{_esc(ref_label)} #</th><th>%</th><th class="num">{_esc(others_label)} #</th><th>%</th><th class="num">Both</th></tr></thead>
        <tbody id="asiCatBody"></tbody>
      </table>
    </div>
    <p class="count-note">A case counts for an engine when at least one of its findings on that case carries this ASI tag. Recalculated live as you edit ASI classes in the explorer.</p>
  </div>

  <h2 id="sec-provenance">Detection rate by provenance (taxonomy, editable)</h2>
  <div class="card">
    <div class="legend">
      <span><span class="legend-dot" style="background:var(--s1)"></span>{_esc(ref_label)}</span>
      <span><span class="legend-dot" style="background:var(--s2)"></span>{_esc(others_label)}</span>
    </div>
    <div class="table-scroll" style="max-height:360px">
      <table class="data-table" id="provCatTable">
        <thead><tr><th>Provenance</th><th class="num">N (union)</th><th class="num">{_esc(ref_label)} #</th><th>%</th><th class="num">{_esc(others_label)} #</th><th>%</th><th class="num">Both</th></tr></thead>
        <tbody id="provCatBody"></tbody>
      </table>
    </div>
    <p class="count-note">Recalculated live as you edit provenance in the explorer.</p>
  </div>
{tier_section}
{org_section}
  <h2 id="sec-lang">Vulnerabilities by skill language</h2>
  <div class="card">
    <p class="count-note">Language detected from the SKILL.md text with a heuristic over Unicode scripts (threshold {LANG_THRESHOLD} characters); everything else falls back to "English / Latin script".</p>
    <div class="table-scroll" style="max-height:360px">
      <table class="data-table" id="langTable">
        <thead><tr><th>Language</th><th class="num">Skills</th><th class="num">{_esc(ref_label)} flagged #</th><th class="num">%</th><th class="num">{_esc(others_label)} flagged #</th><th class="num">%</th><th class="num">{_esc(ref_label)} findings</th><th class="num">{_esc(others_label)} findings</th><th class="num">Total findings</th></tr></thead>
        <tbody>{lang_rows_html}</tbody>
      </table>
    </div>
  </div>

  <h2 id="sec-explorer">Per-skill explorer ({N} rows)</h2>
  <div class="card">
    <div class="filters">
      <input type="text" id="search" placeholder="Search skill name...">
      <select id="langFilter" class="filter-select">
        <option value="">All languages</option>
        {"".join(f'<option value="{_esc(o["name"])}">{_esc(o["name"])} ({o["total"]})</option>' for o in m["by_lang"])}
      </select>
      <select id="asiFilter" class="filter-select">
        <option value="">All ASI classes</option>
        {"".join(f'<option value="{code}">{code} &mdash; {label}</option>' for code, label in ASI_LABELS.items())}
        <option value="UNCLASSIFIED">UNCLASSIFIED</option>
      </select>
      <select id="categoryFilter" class="filter-select">
        <option value="">All categories</option>
        {"".join(f'<option value="{_esc(cat)}">{_esc(cat)} ({d["total"]})</option>' for cat, d in m["by_category"].items())}
      </select>
      <select id="provFilter" class="filter-select">
        <option value="">All provenance</option>
        {"".join(f'<option value="{p}">{p}</option>' for p in PROVENANCE_LABELS)}
      </select>
      <span class="chip active" data-filter="all">All</span>
      <span class="chip" data-filter="both">Both flagged</span>
      <span class="chip" data-filter="ref_only">{_esc(ref_label)} only</span>
      <span class="chip" data-filter="others_only">{_esc(others_label)} only</span>
      <span class="chip" data-filter="neither">Neither</span>
      {engine_chips}
      <span style="flex:1"></span>
      <span class="chip" id="expandAll">Expand all</span>
      <span class="chip" id="collapseAll">Collapse all</span>
    </div>
    <p class="count-note" id="rowcount"></p>
    <p class="filter-badge" id="customFilterBadge" style="display:none"></p>
    <div class="table-flow">
      <table class="data-table" id="skillTable">
        <thead>
          <tr>
            <th></th>
            <th data-key="skill">Skill</th>
            <th data-key="rank" class="num">Rank</th>
            {col_headers}
            <th data-key="bucket">Bucket</th>
          </tr>
        </thead>
        <tbody id="skillBody"></tbody>
      </table>
    </div>
  </div>

  <footer>Generato da postprocess/comparison_report.py dai results.json delle run selezionate. Dato non committato &mdash; rigenera dopo nuove run.</footer>
</div>
</div>

<script id="dataScript">
const DATA = {DATA_JSON};
</script>
<script id="taxoMeta">
const COLS = {COLS_JSON};
const REF = {_js_json(m["ref"])};
const REF_LABEL = {_js_json(ref_label)};
const OTHERS_LABEL = {_js_json(others_label)};
const PROVENANCE_LABELS = {_js_json(PROVENANCE_LABELS)};
const ASI_LABELS = {_js_json(ASI_LABELS)};
const TAXO_N = {N};
const DETAIL_COLSPAN = {detail_colspan};
const STORAGE_KEY = {_js_json("taxonomy_overrides_" + storage_id)};
</script>
<script>
let activeFilter = "all";
let sortKey = null, sortDir = 1;
const OTHER_COLS = COLS.filter(c => !c.is_ref);
const COL_BY_KEY = Object.fromEntries(COLS.map(c => [c.key, c]));

function flagPill(v) {{
  return v ? '<span class="pill pill-flag-yes">flagged</span>' : '<span class="pill pill-flag-no">&mdash;</span>';
}}
function sevPill(s) {{
  if (!s) return '<span class="pill pill-muted">&mdash;</span>';
  const map = {{low:'good', clean:'good', medium:'warning', middle:'warning', high:'serious', critical:'critical'}};
  const status = map[s.toLowerCase()] || 'warning';
  return `<span class="pill pill-${{status}}">${{s}}</span>`;
}}
function bucketLabel(b) {{
  return {{both:'Both', ref_only: REF_LABEL + ' only', others_only: OTHERS_LABEL + ' only', neither:'Neither'}}[b] || b;
}}
function esc(s) {{
  return (s ?? '').toString().replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
}}
function colFindings(r, key) {{
  return (r.cols[key] && r.cols[key].findings) || [];
}}
function allFindings(r) {{
  return COLS.flatMap(c => colFindings(r, c.key));
}}

// ── Taxonomy: override (provenance / ASI / review) in localStorage ──────
function loadOverrides() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}'); }} catch (e) {{ return {{}}; }}
}}
function saveOverrides() {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(OVERRIDES)); }}
let OVERRIDES = loadOverrides();

const FINDING_INDEX = new Map();
DATA.forEach(r => allFindings(r).forEach(f => FINDING_INDEX.set(f.id, f)));

(function hydrateOverrides() {{
  FINDING_INDEX.forEach(f => {{
    const o = OVERRIDES[f.id];
    if (o) {{
      f.provenance = o.provenance;
      f.asi = o.asi;
      if (o.verdict) f.verdict = o.verdict;
      if (o.note !== undefined) f.note = o.note;
    }}
  }});
}})();

function findFindingById(id) {{ return FINDING_INDEX.get(id) || null; }}

function persistFinding(f) {{
  OVERRIDES[f.id] = {{provenance: f.provenance, asi: f.asi, verdict: f.verdict, note: f.note}};
  saveOverrides();
}}

function updateProvenance(id, value) {{
  const f = findFindingById(id);
  if (!f) return;
  f.provenance = value;
  persistFinding(f);
  renderTaxonomy();
  renderCategoryTables();
  render();
}}

function toggleAsi(id, tag) {{
  const f = findFindingById(id);
  if (!f) return;
  const i = f.asi.indexOf(tag);
  if (i >= 0) f.asi.splice(i, 1); else f.asi.push(tag);
  persistFinding(f);
  renderTaxonomy();
  renderCategoryTables();
  render();
}}

function setVerdict(id, value) {{
  const f = findFindingById(id);
  if (!f) return;
  f.verdict = (f.verdict === value) ? 'unreviewed' : value;
  persistFinding(f);
  renderTaxonomy();
  render();
}}

function updateNote(id, value) {{
  const f = findFindingById(id);
  if (!f) return;
  f.note = value;
  persistFinding(f);
}}

function resetClassifications() {{
  if (!confirm('Reset all provenance/ASI/review edits back to auto-classified defaults?')) return;
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
}}

async function saveToFile() {{
  const script = document.getElementById('dataScript');
  script.textContent = 'const DATA = ' + JSON.stringify(DATA).replace(/<\\//g, '<\\\\/') + ';\\n';
  const html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
  if (window.showSaveFilePicker) {{
    try {{
      const handle = await window.showSaveFilePicker({{
        suggestedName: 'comparison_report.html',
        types: [{{description: 'HTML file', accept: {{'text/html': ['.html']}}}}],
      }});
      const writable = await handle.createWritable();
      await writable.write(html);
      await writable.close();
      alert('Saved.');
    }} catch (e) {{
      if (e.name !== 'AbortError') alert('Save failed: ' + e.message);
    }}
  }} else {{
    const blob = new Blob([html], {{type: 'text/html'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'comparison_report.html';
    a.click();
  }}
}}

function findingControlsHtml(f) {{
  const provOpts = PROVENANCE_LABELS.map(p =>
    `<option value="${{p}}" ${{f.provenance === p ? 'selected' : ''}}>${{p}}</option>`).join('');
  const asiChecks = Object.keys(ASI_LABELS).map(a => {{
    const active = f.asi.includes(a);
    return `<label class="asi-check ${{active ? 'active' : ''}}">
      <input type="checkbox" ${{active ? 'checked' : ''}} onchange="toggleAsi('${{f.id}}','${{a}}')">
      <span>${{a}} &mdash; ${{esc(ASI_LABELS[a])}}</span>
    </label>`;
  }}).join('');
  return `<div class="finding-editor">
    <div class="editor-row">
      <span class="editor-label">Provenance</span>
      <select class="prov-select" onchange="updateProvenance('${{f.id}}', this.value)">${{provOpts}}</select>
      <span class="editor-label">Review</span>
      <div class="verdict-group">
        <span class="verdict-btn ${{f.verdict === 'confirmed' ? 'active confirmed' : ''}}" onclick="setVerdict('${{f.id}}','confirmed')">&#10003; Confirm</span>
        <span class="verdict-btn ${{f.verdict === 'disputed' ? 'active disputed' : ''}}" onclick="setVerdict('${{f.id}}','disputed')">&#10007; Dispute</span>
      </div>
    </div>
    <div class="editor-row">
      <span class="editor-label">ASI class</span>
      <div class="asi-check-grid">${{asiChecks}}</div>
    </div>
    <div class="editor-row">
      <span class="editor-label">Note</span>
      <textarea class="note-input" placeholder="Your note on this finding..." onchange="updateNote('${{f.id}}', this.value)">${{esc(f.note || '')}}</textarea>
    </div>
  </div>`;
}}

function taxoDistRows(counts, total, colorVar, labelFn) {{
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return '<p class="muted-text" style="font-size:11px">&mdash;</p>';
  return entries.map(([key, n]) => {{
    const pct = total ? Math.round(n / total * 1000) / 10 : 0;
    const label = labelFn ? labelFn(key) : key;
    return `<div class="taxo-dist-row">
      <div class="taxo-dist-label" title="${{esc(label)}}">${{esc(label)}}</div>
      <div class="taxo-dist-track"><div class="taxo-dist-fill" style="width:${{pct}}%;background:var(${{colorVar}})"></div></div>
      <div class="taxo-dist-val">${{n}}</div>
    </div>`;
  }}).join('');
}}

function asiLabel(code) {{ return ASI_LABELS[code] ? `${{code}} — ${{ASI_LABELS[code]}}` : code; }}
const VERDICT_LABEL = {{unreviewed: 'Unreviewed', confirmed: 'Confirmed', disputed: 'Disputed'}};

function renderTaxonomy() {{
  const grid = document.getElementById('taxoGrid');
  grid.innerHTML = COLS.map(c => {{
    const findings = DATA.flatMap(r => colFindings(r, c.key));
    const flaggedCases = DATA.filter(r => r.cols[c.key] && r.cols[c.key].flagged).length;
    const totalFindings = findings.length;
    const perCase = flaggedCases ? Math.round(totalFindings / flaggedCases * 100) / 100 : 0;
    const scanFailures = TAXO_N - flaggedCases;
    const provCounts = {{}}, asiCounts = {{}}, verdictCounts = {{}};
    findings.forEach(f => {{
      provCounts[f.provenance] = (provCounts[f.provenance] || 0) + 1;
      (f.asi.length ? f.asi : ['UNCLASSIFIED']).forEach(a => {{ asiCounts[a] = (asiCounts[a] || 0) + 1; }});
      verdictCounts[f.verdict] = (verdictCounts[f.verdict] || 0) + 1;
    }});
    return `<div class="taxo-card">
      <h4>${{esc(c.label)}}</h4>
      <div class="taxo-metric"><span class="k">Flagged cases</span><span class="v">${{flaggedCases}} / ${{TAXO_N}}</span></div>
      <div class="taxo-metric"><span class="k">Total findings</span><span class="v">${{totalFindings}}</span></div>
      <div class="taxo-metric"><span class="k">Findings / flagged case</span><span class="v">${{perCase}}</span></div>
      <div class="taxo-metric"><span class="k">Scan failures</span><span class="v">${{scanFailures}} / ${{TAXO_N}}</span></div>
      <div class="taxo-sub">
        <div class="taxo-sub-title">Provenance</div>
        ${{taxoDistRows(provCounts, totalFindings, c.color)}}
        <div class="taxo-sub-title">ASI class</div>
        ${{taxoDistRows(asiCounts, totalFindings, c.color, asiLabel)}}
        <div class="taxo-sub-title">Review status</div>
        ${{taxoDistRows(verdictCounts, totalFindings, c.color, k => VERDICT_LABEL[k] || k)}}
      </div>
    </div>`;
  }}).join('');
}}

// ── Cross-table: riferimento vs "any other", raggruppate per tag ────────
function caseTagSets(getTags) {{
  const acc = {{}};
  DATA.forEach(r => {{
    const refTags = new Set();
    colFindings(r, REF).forEach(f => getTags(f).forEach(t => refTags.add(t)));
    const othTags = new Set();
    OTHER_COLS.forEach(c => colFindings(r, c.key).forEach(f => getTags(f).forEach(t => othTags.add(t))));
    refTags.forEach(t => {{ (acc[t] = acc[t] || {{ref: new Set(), oth: new Set()}}).ref.add(r.key); }});
    othTags.forEach(t => {{ (acc[t] = acc[t] || {{ref: new Set(), oth: new Set()}}).oth.add(r.key); }});
  }});
  return acc;
}}

function renderCrossTable(tbodyId, getTags, labelFn, allTags, clickable) {{
  const acc = caseTagSets(getTags);
  if (allTags) allTags.forEach(t => {{ if (!acc[t]) acc[t] = {{ref: new Set(), oth: new Set()}}; }});
  const rows = Object.entries(acc).map(([tag, sets]) => {{
    let both = 0;
    sets.ref.forEach(s => {{ if (sets.oth.has(s)) both++; }});
    const total = new Set([...sets.ref, ...sets.oth]).size;
    return {{tag, ref: sets.ref.size, oth: sets.oth.size, both, total}};
  }}).sort((a, b) => b.total - a.total);
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = rows.map(row => {{
    const bPct = row.total ? Math.round(row.ref / row.total * 1000) / 10 : 0;
    const sPct = row.total ? Math.round(row.oth / row.total * 1000) / 10 : 0;
    return `<tr class="${{clickable ? 'clickable-row' : ''}}" data-tag="${{esc(row.tag)}}">
      <td>${{esc(labelFn ? labelFn(row.tag) : row.tag)}}</td>
      <td class="num">${{row.total}}</td>
      <td class="num">${{row.ref}}</td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:${{bPct}}%;background:var(--s1)"></div></div>
        <span class="inline-val">${{bPct}}%</span>
      </td>
      <td class="num">${{row.oth}}</td>
      <td>
        <div class="inline-bar"><div class="inline-fill" style="width:${{sPct}}%;background:var(--s2)"></div></div>
        <span class="inline-val">${{sPct}}%</span>
      </td>
      <td class="num">${{row.both}}</td>
    </tr>`;
  }}).join('');
}}

function goToExplorer() {{
  render();
  document.getElementById('sec-explorer').scrollIntoView({{behavior: 'smooth', block: 'start'}});
}}

function renderCategoryTables() {{
  renderCrossTable('asiCatBody', f => (f.asi.length ? f.asi : ['UNCLASSIFIED']), asiLabel, Object.keys(ASI_LABELS), true);
  renderCrossTable('provCatBody', f => [f.provenance], null, PROVENANCE_LABELS, true);
  applyStoredSort('asiCatTable');
  applyStoredSort('provCatTable');
  document.getElementById('asiCatBody').querySelectorAll('tr[data-tag]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      document.getElementById('asiFilter').value = tr.dataset.tag;
      goToExplorer();
    }});
  }});
  document.getElementById('provCatBody').querySelectorAll('tr[data-tag]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      document.getElementById('provFilter').value = tr.dataset.tag;
      goToExplorer();
    }});
  }});
}}

function initClickThroughTables() {{
  document.querySelectorAll('#orgTable tbody tr[data-org]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      document.getElementById('search').value = tr.dataset.org;
      goToExplorer();
    }});
  }});
  document.querySelectorAll('#langTable tbody tr[data-lang]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      document.getElementById('langFilter').value = tr.dataset.lang;
      goToExplorer();
    }});
  }});
  document.querySelectorAll('#categoryTable tbody tr[data-cat]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      document.getElementById('categoryFilter').value = tr.dataset.cat;
      goToExplorer();
    }});
  }});
  document.querySelectorAll('#tierTable tbody tr[data-lo]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      tierFilter = {{lo: parseInt(tr.dataset.lo, 10), hi: parseInt(tr.dataset.hi, 10)}};
      goToExplorer();
    }});
  }});
  document.querySelectorAll('.codes-col tbody tr[data-code]').forEach(tr => {{
    tr.addEventListener('click', () => {{
      codeFilter = {{engine: tr.dataset.engine, code: tr.dataset.code}};
      goToExplorer();
    }});
  }});
}}

// ── Sort generico per le tabelle statiche (non l'explorer) ──────────────
const tableSortState = new Map();

function cellSortValue(td) {{
  if (!td) return '';
  const text = td.textContent.trim();
  if (text === '' || text === '\\u2014') return -Infinity;
  const primary = text.split('(')[0].trim().replace(/,/g, '').replace('%', '');
  if (primary !== '' && !isNaN(primary)) return parseFloat(primary);
  return text.toLowerCase();
}}

function sortTableRows(table, keys) {{
  const tbody = table.tBodies[0];
  if (!tbody || !keys.length) return;
  const rows = Array.from(tbody.rows);
  rows.sort((a, b) => {{
    for (const {{col, dir}} of keys) {{
      const av = cellSortValue(a.cells[col]);
      const bv = cellSortValue(b.cells[col]);
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
    }}
    return 0;
  }});
  rows.forEach(r => tbody.appendChild(r));
  Array.from(table.tHead.rows[0].cells).forEach((th, i) => {{
    const rank = keys.findIndex(k => k.col === i);
    const k = rank >= 0 ? keys[rank] : null;
    th.classList.toggle('sort-active', !!k);
    const arrow = th.querySelector('.sort-arrow');
    if (arrow) {{
      arrow.textContent = k ? (k.dir === 1 ? '\\u25B2' : '\\u25BC') + (keys.length > 1 ? String(rank + 1) : '') : '';
    }}
  }});
}}

function applyStoredSort(tableId) {{
  const table = document.getElementById(tableId);
  const keys = tableSortState.get(tableId);
  if (table && keys && keys.length) sortTableRows(table, keys);
}}

function makeSortableTable(table) {{
  if (!table.id || !table.tHead) return;
  Array.from(table.tHead.rows[0].cells).forEach((th, colIdx) => {{
    th.classList.add('sortable-th');
    th.title = 'Click: sort by this column. Shift+click: add as secondary sort key.';
    th.appendChild(Object.assign(document.createElement('span'), {{className: 'sort-arrow'}}));
    th.addEventListener('click', (ev) => {{
      let keys = tableSortState.get(table.id) || [];
      const idx = keys.findIndex(k => k.col === colIdx);
      if (ev.shiftKey) {{
        keys = idx >= 0
          ? keys.map((k, i) => i === idx ? {{col: colIdx, dir: -k.dir}} : k)
          : keys.concat([{{col: colIdx, dir: 1}}]);
      }} else {{
        const dir = (idx === 0 && keys.length === 1) ? -keys[0].dir : 1;
        keys = [{{col: colIdx, dir}}];
      }}
      tableSortState.set(table.id, keys);
      sortTableRows(table, keys);
    }});
  }});
}}

function initSortableTables() {{
  document.querySelectorAll('table.data-table').forEach(t => {{
    if (t.id !== 'skillTable') makeSortableTable(t);
  }});
}}

document.getElementById('saveReportBtn').addEventListener('click', saveToFile);
document.getElementById('resetClassBtn').addEventListener('click', resetClassifications);

function matchesFilter(r) {{
  if (activeFilter === 'all') return true;
  if (activeFilter.startsWith('eng::')) {{
    const key = activeFilter.slice(5);
    return !!(r.cols[key] && r.cols[key].flagged);
  }}
  return r.bucket === activeFilter;
}}

function matchesLang(r) {{
  const lang = document.getElementById('langFilter').value;
  return !lang || r.lang === lang;
}}

function matchesAsi(r) {{
  const code = document.getElementById('asiFilter').value;
  if (!code) return true;
  return allFindings(r).some(f => code === 'UNCLASSIFIED' ? f.asi.length === 0 : f.asi.includes(code));
}}

function matchesCategory(r) {{
  const cat = document.getElementById('categoryFilter').value;
  if (!cat) return true;
  if (cat.startsWith('no ') && cat.endsWith(' finding (miss)')) return (r.categories || []).includes('user_provided');
  return (r.categories || []).includes(cat);
}}

function matchesProv(r) {{
  const p = document.getElementById('provFilter').value;
  if (!p) return true;
  return allFindings(r).some(f => f.provenance === p);
}}

let codeFilter = null;
let tierFilter = null;

function matchesCode(r) {{
  if (!codeFilter) return true;
  return colFindings(r, codeFilter.engine).some(f => (f.code || f.type) === codeFilter.code);
}}

function matchesTier(r) {{
  if (!tierFilter) return true;
  const rank = parseInt(r.rank ?? 0, 10) || 0;
  return rank >= tierFilter.lo && rank < tierFilter.hi;
}}

function hasSecondaryFilter() {{
  return !!document.getElementById('search').value.trim()
    || !!document.getElementById('langFilter').value
    || !!document.getElementById('asiFilter').value
    || !!document.getElementById('categoryFilter').value
    || !!document.getElementById('provFilter').value
    || !!codeFilter || !!tierFilter;
}}

function resetAllFilters() {{
  document.getElementById('search').value = '';
  document.getElementById('langFilter').value = '';
  document.getElementById('asiFilter').value = '';
  document.getElementById('categoryFilter').value = '';
  document.getElementById('provFilter').value = '';
  codeFilter = null;
  tierFilter = null;
  activeFilter = 'all';
}}

function syncChipUI() {{
  document.querySelectorAll('.chip[data-filter]').forEach(c => {{
    c.classList.toggle('active', c.dataset.filter === 'all'
      ? (activeFilter === 'all' && !hasSecondaryFilter())
      : activeFilter === c.dataset.filter);
  }});
  const badge = document.getElementById('customFilterBadge');
  if (!badge) return;
  const parts = [];
  const q = document.getElementById('search').value.trim();
  if (q) parts.push(`search "${{q}}"`);
  const lang = document.getElementById('langFilter').value;
  if (lang) parts.push(`language = ${{lang}}`);
  const asi = document.getElementById('asiFilter').value;
  if (asi) parts.push(`ASI = ${{asi}}`);
  const cat = document.getElementById('categoryFilter').value;
  if (cat) parts.push(`category = ${{cat}}`);
  const prov = document.getElementById('provFilter').value;
  if (prov) parts.push(`provenance = ${{prov}}`);
  if (codeFilter) parts.push(`code = ${{codeFilter.code}} (${{(COL_BY_KEY[codeFilter.engine] || {{}}).label || codeFilter.engine}})`);
  if (tierFilter) parts.push(`rank ${{tierFilter.lo}}-${{tierFilter.hi}}`);
  if (parts.length) {{
    badge.textContent = 'Custom filter: ' + parts.join(', ') + ' (click "All" to reset)';
    badge.style.display = '';
  }} else {{
    badge.style.display = 'none';
  }}
}}

const expanded = new Set();
const sectionState = new Map();
function sectionOpen(key, defaultOpen) {{
  return sectionState.has(key) ? sectionState.get(key) : defaultOpen;
}}

function engineSection(col, r) {{
  const findings = colFindings(r, col.key);
  const key = `${{r.key}}::${{col.key}}`;
  const open = sectionOpen(key, true) ? 'open' : '';
  if (!findings.length) {{
    return `<details class="detail-section" data-key="${{esc(key)}}" style="border-left-color:var(${{col.color}})" ${{open}}>
      <summary>${{esc(col.label)}}</summary><p class="muted-text">Clean &mdash; no findings.</p></details>`;
  }}
  const items = findings.map(f => `
    <div class="finding-item ${{f.verdict === 'confirmed' ? 'verdict-confirmed' : f.verdict === 'disputed' ? 'verdict-disputed' : ''}}">
      ${{sevPill(f.severity)}} ${{f.code ? `<span class="mono">${{esc(f.code)}}</span>` : ''}}
      <strong>${{esc(f.title || f.type || '')}}</strong>
      ${{f.description ? `<p>${{esc(f.description)}}</p>` : ''}}
      ${{f.quote ? `<blockquote>${{esc(f.quote)}}</blockquote>` : ''}}
      ${{findingControlsHtml(f)}}
    </div>`).join('');
  return `<details class="detail-section" data-key="${{esc(key)}}" style="border-left-color:var(${{col.color}})" ${{open}}><summary>${{esc(col.label)}} (${{findings.length}})</summary><div class="detail-section-body">${{items}}</div></details>`;
}}

function skillMdSection(r) {{
  const key = `${{r.key}}::skillmd`;
  const open = sectionOpen(key, false) ? 'open' : '';
  if (!r.skill_content) {{
    return `<details class="detail-section" data-key="${{esc(key)}}" style="border-left-color:var(--muted)" ${{open}}><summary>SKILL.md</summary><p class="muted-text">No content recorded.</p></details>`;
  }}
  const lines = r.skill_content.split('\\n').length;
  return `<details class="detail-section" data-key="${{esc(key)}}" style="border-left-color:var(--muted)" ${{open}}><summary>SKILL.md (${{lines}} lines, ${{r.skill_content.length}} chars)</summary><div class="detail-section-body"><pre class="skillmd-pre">${{esc(r.skill_content)}}</pre></div></details>`;
}}

function patchSection(r) {{
  const key = `${{r.key}}::patch`;
  const open = sectionOpen(key, false) ? 'open' : '';
  if (!r.patches_applied.length) return '';
  const items = r.patches_applied.map((p, i) => `
    <div class="patch-item">
      <div class="patch-num">Patch ${{i + 1}}</div>
      <div class="diff-removed"><div class="diff-label">Removed</div><pre>${{esc(p.original)}}</pre></div>
      <div class="diff-added"><div class="diff-label">Replaced with</div><pre>${{esc(p.replacement)}}</pre></div>
    </div>`).join('');
  const reasoning = r.patch_reasoning ? `<p class="muted-text patch-reasoning">${{esc(r.patch_reasoning)}}</p>` : '';
  return `<details class="detail-section" data-key="${{esc(key)}}" style="border-left-color:var(--muted)" ${{open}}><summary>${{esc(REF_LABEL)}} &mdash; patch (${{r.patches_applied.length}})</summary><div class="detail-section-body">${{reasoning}}${{items}}</div></details>`;
}}

function detailHtml(r) {{
  return `<td colspan="${{DETAIL_COLSPAN}}"><div class="detail-panel">
    ${{skillMdSection(r)}}
    ${{COLS.map(c => engineSection(c, r)).join('')}}
    ${{patchSection(r)}}
  </div></td>`;
}}

function visibleRows() {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  return DATA.filter(r => matchesFilter(r) && matchesLang(r) && matchesAsi(r) && matchesCategory(r)
    && matchesProv(r) && matchesCode(r) && matchesTier(r)
    && (!q || (r.skill || '').toLowerCase().includes(q)));
}}

function sortValue(r, key) {{
  if (key === 'skill' || key === 'rank' || key === 'bucket') return r[key];
  const c = r.cols[key];
  return c ? (c.flagged ? 1 : 0) : 0;
}}

function render() {{
  syncChipUI();
  let rows = visibleRows();
  if (sortKey) {{
    rows = rows.slice().sort((a, b) => {{
      let av = sortValue(a, sortKey), bv = sortValue(b, sortKey);
      if (typeof av === 'boolean') {{ av = av ? 1 : 0; bv = bv ? 1 : 0; }}
      if (av < bv) return -1 * sortDir;
      if (av > bv) return 1 * sortDir;
      return 0;
    }});
  }}
  document.getElementById('rowcount').textContent = `${{rows.length}} of ${{DATA.length}} skills`;
  const body = document.getElementById('skillBody');
  body.innerHTML = rows.map(r => {{
    const isOpen = expanded.has(r.key);
    const cells = COLS.map(c => {{
      const d = r.cols[c.key] || {{}};
      if (c.is_ref) {{
        return `<td>${{d.flagged ? sevPill(d.top_sev) : '<span class="pill pill-muted">clean</span>'}}</td>`;
      }}
      return `<td>${{flagPill(d.flagged)}}${{d.top_code ? ` <span class="muted-text mono">${{esc(d.top_code)}}</span>` : ''}}</td>`;
    }}).join('');
    const main = `
    <tr class="row-main" data-key="${{esc(r.key)}}">
      <td class="chevron">${{isOpen ? '&#9662;' : '&#9656;'}}</td>
      <td>${{esc(r.skill)}}</td>
      <td class="num">${{r.rank ?? '&mdash;'}}</td>
      ${{cells}}
      <td>${{esc(bucketLabel(r.bucket))}}</td>
    </tr>`;
    const detail = isOpen ? `<tr class="row-detail">${{detailHtml(r)}}</tr>` : '';
    return main + detail;
  }}).join('');
  body.querySelectorAll('details.detail-section[data-key]').forEach(d => {{
    d.addEventListener('toggle', () => sectionState.set(d.dataset.key, d.open));
  }});
  body.querySelectorAll('tr.row-main').forEach(tr => {{
    tr.addEventListener('click', () => {{
      const k = tr.dataset.key;
      if (expanded.has(k)) expanded.delete(k); else expanded.add(k);
      render();
    }});
  }});
}}

document.querySelectorAll('.chip[data-filter]').forEach(chip => {{
  chip.addEventListener('click', () => {{
    if (chip.dataset.filter === 'all') {{
      resetAllFilters();
    }} else {{
      activeFilter = chip.dataset.filter;
    }}
    render();
  }});
}});
document.getElementById('search').addEventListener('input', render);
document.getElementById('langFilter').addEventListener('change', render);
document.getElementById('asiFilter').addEventListener('change', render);
document.getElementById('categoryFilter').addEventListener('change', render);
document.getElementById('provFilter').addEventListener('change', render);
document.querySelectorAll('#skillTable th[data-key]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.key;
    sortDir = (sortKey === key) ? -sortDir : 1;
    sortKey = key;
    render();
  }});
}});
document.getElementById('expandAll').addEventListener('click', () => {{
  visibleRows().forEach(r => expanded.add(r.key));
  render();
}});
document.getElementById('collapseAll').addEventListener('click', () => {{
  expanded.clear();
  render();
}});

function toggleTheme() {{
  const html = document.documentElement;
  html.setAttribute('data-theme', html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}}

renderTaxonomy();
renderCategoryTables();
render();
initSortableTables();
initClickThroughTables();
</script>
</body>
</html>
'''


# ── Entry point ──────────────────────────────────────────────────────────
def generate(run_dirs, output_dir, title: str | None = None, ref: str | None = None) -> dict:
    """Genera <output_dir>/comparison_report.html + comparison_data.json."""
    out = Path(output_dir)
    if not out.is_absolute():
        out = BASE / out
    out.mkdir(parents=True, exist_ok=True)

    model = build_model(run_dirs, ref=ref, title=title)
    html = render_html(model, storage_id=out.name)

    html_path = out / "comparison_report.html"
    json_path = out / "comparison_data.json"
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "html": str(html_path),
        "json": str(json_path),
        "n": model["n"],
        "title": model["title"],
        "columns": [{"key": c["key"], "label": c["label"], "is_ref": c["is_ref"]} for c in model["columns"]],
        "overview": model["overview"],
        "agreement": model["agreement"],
        "meta": model["meta"],
    }


def main():
    ap = argparse.ArgumentParser(description="Report comparativo su N run con lo stesso dataset")
    ap.add_argument("--runs", nargs="+", required=True, help="cartelle di run (con results.json)")
    ap.add_argument("--output", required=True, help="cartella di output del report")
    ap.add_argument("--title", default=None)
    ap.add_argument("--ref", default=None, help="colonna di riferimento: <run_id>:<engine> o <engine>")
    args = ap.parse_args()

    res = generate(args.runs, args.output, title=args.title, ref=args.ref)
    print(f"N={res['n']}  colonne={[c['label'] for c in res['columns']]}")
    print("overview:", {o["label"]: f"{o['flagged']} ({o['rate']}%)" for o in res["overview"]})
    print("agreement:", res["agreement"])
    print("Wrote", res["html"])


if __name__ == "__main__":
    main()
