"""
Pipeline: Custom (5ª modalità, configurabile a runtime)
=======================================================
Compone a runtime una qualsiasi combinazione VALIDA dei 4 step esistenti
(fonte skill → difesa → eval → tester) secondo una PipelineConfig, riusando gli
agenti/nodi già implementati invece di duplicarli. Le 4 pipeline fisse restano
intatte: questa è un layer di orchestrazione CONDIZIONALE sopra moduli esistenti.

    source ──(difesa?)──► motori ──(eval?)──► eval ──(tester?)──► tester ──► report
       │                    │                                        │
       │                    └─ blue | skillspector | cisco |         └─ all | blue_gap_only
       │                       snyk | skills_sh  (uno o più)
       └─ red | skill_inject | local_preinjected | online

Riuso diretto (nessuna reimplementazione):
  • fonte red          → graph.node_red (agents.generate) su skill pulite selezionate
  • fonte skill_inject → agents.skill_inject_loader.load_records (come blue-eval)
  • fonte local        → graph.node_load_external_skills
  • difesa             → graph.node_blue / node_skillspector / node_cisco / node_snyk /
                         node_skills_sh, uno per motore selezionato
  • eval               → pipelines.blue_eval.classify (Tier 1 fuzzy + Tier 2 LLM)
  • tester             → graph.node_tester_judge (three-/two-way nativo, affinity queue)
  • blue_gap_only      → filtro/merge generalizzato da blue_eval_testing
  • report             → benchmark._compute_stats + _write_* (come tutte le pipeline)

Orchestrazione imperativa con merge shallow manuale (state.update(node(state))),
equivalente al merge di LangGraph ma più leggibile per il branching condizionale.
"""
from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from pathlib import Path

import core.cli_output as cli
from graph import (
    SSE3State,
    node_red, node_blue, node_snyk, node_skillspector, node_cisco, node_aig, node_skill_vetter, node_skills_sh,
    node_load_external_skills, node_tester_judge,
)
from graph.nodes import _record_sort_key
from pipelines.custom_config import (
    PipelineConfig, validate_or_raise, find_ground_truth_json, clean_engines,
    clean_no_llm,
)


BASE = Path(__file__).resolve().parent.parent


# ── Helper merge (replica il merge shallow di LangGraph) ───────────────

def _merge(state: dict, update: dict | None) -> dict:
    if update:
        state.update(update)
    return state


# ── Step FONTE ─────────────────────────────────────────────────────────

def _source_red(state: SSE3State, cfg: PipelineConfig) -> dict:
    """Red Agent su skill pulite selezionate da una cartella locale.
    Ground truth = inj_text generato. BASE three-way = il file sorgente pulito."""
    from agents.red_agent import load_catalog

    folder = Path(cfg.source.local_folder_path or "")
    files  = [folder / f for f in (cfg.source.selected_files or [])]
    skill_contents: dict[str, str] = {}
    src_by_skill:   dict[str, str] = {}
    for p in files:
        if not p.exists():
            cli.warn(f"[custom/red] file non trovato: {p}")
            continue
        name = p.stem if p.stem.lower() != "skill" else p.parent.name
        skill_contents[name] = p.read_text(encoding="utf-8", errors="ignore")
        src_by_skill[name]   = str(p.resolve())
    if not skill_contents:
        return {"error": "[custom/red] nessun file skill valido selezionato."}

    # Profilo skill-inject (checkbox webui): tassonomia = 8 classi del paper +
    # KB di esempi (le injection direct di skill-inject). Accoppiati: il flag
    # attiva SIA il catalog paper SIA la KB.
    use_kb  = bool(getattr(cfg.source, "use_skill_inject_kb", False))
    red_kb  = None
    if use_kb:
        catalog = load_catalog(BASE / "config" / "catalog_paper.json")
        from agents.red_kb import build_kb
        red_kb  = build_kb(BASE / "skill-inject")
        if not red_kb:
            cli.warn("[custom/red] KB skill-inject vuota — proseguo senza esempi.")
    else:
        catalog = load_catalog(BASE / "config" / "catalog.json")

    # Filtri difficoltà (K1/K2/K3) e tipologia vulnerabilità: riducono le combo
    # vuln×diff generate dal Red.
    diffs = cfg.source.red_difficulties
    if diffs:
        want = {str(d).upper() for d in diffs}
        catalog["difficulty_levels"] = [d for d in catalog["difficulty_levels"]
                                        if str(d["id"]).upper() in want]
        if not catalog["difficulty_levels"]:
            return {"error": "[custom/red] nessuna difficoltà valida selezionata (K1/K2/K3)."}
    # Con la KB attiva la tassonomia è quella del paper (8 classi): il filtro
    # red_vuln_types usa gli id "nostri" e non si applica → ignorato.
    vts = None if use_kb else cfg.source.red_vuln_types
    if vts:
        want_v = {str(v).lower() for v in vts}
        catalog["vulnerability_types"] = [v for v in catalog["vulnerability_types"]
                                          if str(v["id"]).lower() in want_v]
        if not catalog["vulnerability_types"]:
            return {"error": "[custom/red] nessuna tipologia di vulnerabilità valida selezionata."}

    cli.start_run()
    cli.header(scope=",".join(sorted(skill_contents)), injections="n/a",
               attempts=state.get("max_attempts", 5),
               parallel=state.get("parallel", 4), vuln_types=[])

    # max_files = cap GLOBALE sul totale di injection (coerente con skill_inject e
    # con il significato "all pipelines" del campo). node_red lo consuma skill-per-skill
    # (max_files_global=True): niente over-generazione (il Red genera al più `mf` file),
    # niente ceil/×2, e le classi restano complete sulle prime skill.
    sub = {**state, "skill_contents": skill_contents, "catalog": catalog,
           "red_kb": red_kb, "max_files_global": True}

    out = node_red(sub)
    if out.get("error"):
        return out
    injs = out.get("injections", []) or []
    # Safety net: node_red rispetta già il cap globale; tronchiamo solo per sicurezza.
    mf = state.get("max_files")
    if mf and len(injs) > int(mf):
        injs = injs[:int(mf)]
        out["injections"] = injs
    # BASE pulita per il Tester three-way: il SKILL.md sorgente da cui Red ha iniettato.
    for r in injs:
        r["base_skill_path"] = src_by_skill.get(r.get("skill"))
        r.setdefault("injected_text", r.get("inj_text", ""))  # ground truth per l'eval
    return out


def _source_skill_inject(state: SSE3State, cfg: PipelineConfig) -> dict:
    """Ricette deterministiche skill-inject (come blue-eval), con filtro opzionale
    per skill-file (es. docx, calendar). Ground truth = injected_text dalla ricetta."""
    from agents.skill_inject_loader import load_records

    si_path = Path(cfg.source.skill_inject_path or "skill-inject")
    if not si_path.is_absolute():
        si_path = BASE / si_path
    cats    = cfg.source.skill_inject_categories or ["obvious", "contextual"]
    skills_f = cfg.source.skill_inject_skills or None
    output_dir = state["output_dir"]

    if not si_path.exists():
        return {"error": f"[custom/skill_inject] skill-inject non trovato: {si_path}"}

    cli.start_run()
    records = load_records(si_path, cats, skills_f, types_filter=["direct"],
                           max_files=state.get("max_files"))
    if not records:
        return {"error": "[custom/skill_inject] nessun record (controlla categorie/skill)."}

    inj_dir = output_dir / "injected"
    for i, r in enumerate(records):
        p = inj_dir / f"{r['injection_id']}__{r['skill']}_{i}" / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(r["injected_content"], encoding="utf-8")
        r["inj_path"] = str(p)
        # Mappa i campi skill-inject sui campi generici usati da blue/tester/report.
        r["vuln_type"]       = r.get("category", "")
        r["difficulty"]      = r.get("type", "")
        r["inj_text"]        = r.get("injected_text", "")
        r["base_skill_path"] = r.get("skill_path") or r["inj_path"]
        r.pop("injected_content", None)
        r.pop("base_content", None)

    cli.header(scope=",".join(sorted(set(cats))), injections=len(records),
               attempts=state.get("max_attempts", 5),
               parallel=state.get("parallel", 4),
               vuln_types=sorted({r["skill"] for r in records}))
    return {"injections": records, "error": None}


def _github_raw_url(url: str) -> tuple[str | None, str | None]:
    """Converte un URL della webapp GitHub (blob) nel corrispondente raw-content
    URL. urlopen() su un URL github.com/.../blob/... scarica la PAGINA HTML del
    viewer (React SPA), non il markdown — un errore silenzioso che finiva dritto
    dentro il SKILL.md scritto su disco (visto in produzione: 450KB di HTML dove
    doveva esserci un file di poche righe).

    Ritorna (raw_url, None) se convertibile, o se l'URL non è affatto github.com
    (host generico → passthrough, invariato: raw.githubusercontent.com e altri
    host restano gestiti come prima). Ritorna (None, errore) se l'URL È github.com
    ma non punta a un singolo file (root del repo, /tree/ di una cartella): non
    esiste un raw-content per quei path, e scaricarli scaricherebbe di nuovo la
    pagina HTML del viewer.
    """
    p = urllib.parse.urlparse(url)
    if p.netloc not in ("github.com", "www.github.com"):
        return url, None
    parts = [s for s in p.path.split("/") if s]
    # github.com/<user>/<repo>/blob/<branch>/<path...>
    if len(parts) >= 5 and parts[2] == "blob":
        user, repo, branch = parts[0], parts[1], parts[3]
        file_path = "/".join(parts[4:])
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}", None
    return None, ("GitHub URL doesn't point to a single file (needs a 'blob' link, "
                  "e.g. .../blob/main/path/SKILL.md) — repo root or folder can't "
                  "be downloaded as a single skill")


def _source_online(state: SSE3State, cfg: PipelineConfig) -> dict:
    """Scarica SKILL.md da URL esterne. Ground truth non nota (no eval).
    Senza BASE pulita: il Tester gira sul file scaricato (BASE==INJECTED)."""
    urls = [u.strip() for u in (cfg.source.urls or []) if (u or "").strip()]
    inj_dir = state["output_dir"] / "injected"
    cli.start_run()
    cli.phase("fetch", "downloading skills from URLs")
    injections = []
    for i, url in enumerate(urls):
        fetch_url, err = _github_raw_url(url)
        if err:
            cli.warn(f"[custom/online] {url}: {err}")
            continue
        try:
            req = urllib.request.Request(fetch_url, headers={"User-Agent": "SSE-custom/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode("utf-8", "replace")
        except Exception as e:
            cli.warn(f"[custom/online] fetch failed for {url}: {e}")
            continue
        # Guardia generica (non solo GitHub): se malgrado tutto arriva una pagina
        # HTML (404 raw servito come pagina, altro host con lo stesso problema),
        # non scriverla come se fosse contenuto skill — scartare è meglio che
        # produrre un finto SKILL.md pieno di markup.
        if content.lstrip()[:15].lower().startswith(("<!doctype html", "<html")):
            cli.warn(f"[custom/online] {url}: HTML response instead of skill "
                     f"content (wrong URL?) — skipping")
            continue
        name = Path(urllib.parse.urlparse(url).path).stem or f"url_{i}"
        p = inj_dir / f"online_{i}__{name}" / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        injections.append({"skill": name, "vuln_type": "online", "difficulty": "—",
                           "inj_path": str(p), "source_url": url})
        cli.item(f"{len(injections)}/{len(urls)} {name}")
    cli.phase_done(timed=False)
    if not injections:
        return {"error": "[custom/online] nessuna skill scaricata."}
    cli.header(scope="online", injections=len(injections),
               attempts=state.get("max_attempts", 5),
               parallel=state.get("parallel", 4), vuln_types=[])
    return {"injections": injections, "error": None}


def _attach_ground_truth(records: list[dict], folder_path: str | None) -> int:
    """Per la fonte local_preinjected: se la cartella contiene un JSON di ground
    truth (mappa nome-file → injection), lo aggancia ai record caricati così da
    sbloccare l'eval. Match per basename del file, poi stem, poi nome skill.

    Formato del valore nel JSON, flessibile:
      • stringa            → il testo dell'injection;
      • dict               → campo 'injection' | 'inj_text' | 'injected_text',
                              più metadati opzionali (vuln_type/category,
                              difficulty, title, injection_id) riportati sul record.
    Ritorna il numero di record agganciati."""
    gt_path = find_ground_truth_json(folder_path)
    if not gt_path:
        return 0
    try:
        data = json.loads(Path(gt_path).read_text(encoding="utf-8"))
    except Exception as e:
        cli.warn(f"[custom/local] ground truth JSON illeggibile ({gt_path}): {e}")
        return 0
    if not isinstance(data, dict):
        cli.warn(f"[custom/local] ground truth JSON non è una mappa nome-file→injection: {gt_path}")
        return 0

    def _text(v) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("injection") or v.get("inj_text") or v.get("injected_text") or ""
        return ""

    matched = 0
    for r in records:
        p = Path(r.get("inj_path", ""))
        entry = data.get(p.name) or data.get(p.stem) or data.get(r.get("skill", ""))
        txt = _text(entry)
        if not txt:
            continue
        r["injected_text"] = txt
        r["inj_text"]      = txt
        if isinstance(entry, dict):
            # Promuovi i metadati noti (migliora grouping del report/eval).
            vt = entry.get("vuln_type") or entry.get("category")
            if vt:               r["vuln_type"]    = vt
            if entry.get("difficulty"):   r["difficulty"]   = entry["difficulty"]
            if entry.get("title"):        r["title"]        = entry["title"]
            if entry.get("injection_id"): r["injection_id"] = entry["injection_id"]
            if entry.get("skill"):        r["skill"]        = entry["skill"]
        matched += 1

    cli.debug(f"  🎯 ground truth: {matched}/{len(records)} file agganciati da "
              f"{Path(gt_path).name}")
    if matched < len(records):
        cli.warn(f"[custom/local] {len(records) - matched} file senza ground truth "
                 "nel JSON: l'eval li tratterà come privi di injection nota.")
    return matched


def node_custom_source(state: SSE3State, cfg: PipelineConfig) -> dict:
    cli.phase("source", f"resolving skills · {cfg.source.type}")
    cli.phase_done(timed=False)
    st = cfg.source.type
    if st == "red":
        return _source_red(state, cfg)
    if st == "skill_inject":
        return _source_skill_inject(state, cfg)
    if st == "local_preinjected":
        # node_load_external_skills materializza già injections con inj_path.
        out = node_load_external_skills(
            {**state, "external_skill_paths":
                [str(Path(cfg.source.local_folder_path or "") / f)
                 for f in (cfg.source.selected_files or [])]})
        # Se la cartella porta un JSON di ground truth, aggancialo: sblocca l'eval.
        if not out.get("error"):
            _attach_ground_truth(out.get("injections", []) or [],
                                 cfg.source.local_folder_path)
        return out
    if st == "online":
        return _source_online(state, cfg)
    return {"error": f"[custom] fonte sconosciuta: {st}"}


# ── Step EVAL (riusa la classificazione a due livelli di blue-eval) ────

def node_custom_eval(state: SSE3State) -> dict:
    """Classifica TP/FP/FN i finding del Blue contro il ground truth (Tier 1
    fuzzy + Tier 2 validator LLM). Identica logica di blue-eval, esposta come
    step opzionale. Per costruzione qui blue=true e ground truth nota.

    Parallelizzato come pipelines/blue_eval.py: il Tier 2 è una chiamata LLM
    bloccante per ogni caso ambiguo, e in sequenza dominava il tempo dello step.
    Il Tier 1 è puro calcolo locale, quindi i worker restano quasi tutti liberi.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pipelines.blue_eval import classify

    records  = state.get("injections", []) or []
    parallel = max(1, int(state.get("parallel", 4) or 4))
    cli.phase("eval", "scoring detection (auto-match · LLM review for ambiguous)")
    counts = {"TP": 0, "FP": 0, "FN": 0}
    lock   = threading.Lock()

    def _classify_one(idx: int) -> tuple[int, dict]:
        r = records[idx]
        # classify legge record["injected_text"] come ground truth.
        r.setdefault("injected_text", r.get("inj_text", ""))
        blue = {"findings": r.get("findings", []),
                "patches_applied": r.get("patches_applied", [])}
        return idx, classify(r, blue)

    with ThreadPoolExecutor(max_workers=parallel) as ex:
        futs = {ex.submit(_classify_one, i): i for i in range(len(records))}
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                _i, res = fut.result()
            except Exception as e:
                # Stesso fallback di blue_eval.node_blue_eval: il record resta nel
                # run, marcato come mancato, invece di far cadere l'intero step.
                res = {"verdict": "FN", "tier": 1, "ratio": 0.0, "blue_quote": "",
                       "patch_removed": "", "patch_added": "",
                       "reasoning": f"classify error: {e}",
                       "blue_findings_count": 0, "unmatched_findings": 0}
                cli.warn(f"Classify error: {e}")
            r = records[i]
            r.update({
                "verdict":             res["verdict"],
                "tier":                res["tier"],
                "match_ratio":         res["ratio"],
                "blue_quote":          res["blue_quote"],
                "patch_removed":       res["patch_removed"],
                "patch_added":         res["patch_added"],
                "validator_reasoning": res["reasoning"],
                "blue_findings_count": res.get("blue_findings_count", 0),
                "unmatched_findings":  res.get("unmatched_findings", 0),
            })
            with lock:
                counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
                snap = dict(counts)
            cli.item(f"{r.get('skill')} {r.get('vuln_type')} → {res['verdict']}  "
                     f"caught {snap['TP']} · missed {snap['FN']} · false-alarm {snap['FP']}")
    cli.phase_done()
    return {"injections": records}


# ── Step TESTER scope=blue_gap_only (generalizzazione di blue-eval-testing) ─

def _is_blue_gap(r: dict) -> bool:
    """'Gap' = caso che il Blue non ha rilevato/patchato. Con eval attivo equivale
    a verdict != 'TP' (parità con blue-eval-testing); senza eval generalizza a
    'nessuna patch applicata e non rilevato' — indipendente dalla fonte."""
    if r.get("verdict"):
        return r.get("verdict") != "TP"
    return not r.get("patches_applied") and not r.get("detected")


def _run_tester(state: SSE3State, scope: str) -> dict:
    """Esegue node_tester_judge su tutti i record (scope='all') o solo sui 'gap'
    del Blue (scope='blue_gap_only'), ricomponendo i non testati per il report."""
    records = state.get("injections", []) or []
    if scope != "blue_gap_only":
        return node_tester_judge(state)

    gap      = [r for r in records if _is_blue_gap(r)]
    non_gap  = [r for r in records if not _is_blue_gap(r)]
    cli.phase("filter", "selecting Blue's gaps for testing")
    cli.item(f"{len(gap)}/{len(records)} to test (Blue gaps) · {len(non_gap)} skipped")
    cli.phase_done(timed=False)
    if not gap:
        return {"injections": records}   # niente da testare → report diretto
    out = node_tester_judge({**state, "injections": gap})
    tested = out.get("injections", gap)
    # I non testati restano senza metriche ASR (asr_pre=None) → esclusi dai
    # denominatori ASR ma presenti nel report (come in blue-eval-testing).
    merged = list(tested) + non_gap
    merged.sort(key=_record_sort_key)
    return {"injections": merged}


# ── Step REPORT (riusa _compute_stats + _write_* come ogni pipeline) ──

def node_custom_report(state: SSE3State, steps: dict) -> dict:
    # Import locale: la root del progetto è già in sys.path (l'entry point vive
    # lì), quindi non serve manipolarlo.
    from reporting.report import _compute_stats, _write_report, _write_pdf, _write_html

    injections = state.get("injections", []) or []
    output_dir = state["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    cli.phase("report", "writing MD / HTML / PDF")
    data = _compute_stats(injections, state)
    # Mark the pipeline and attach the executed-steps summary for reproducibility.
    # NOTE: this is stored in results.json only — it is NOT appended to run_notes,
    # which stays exactly what the user wrote.
    data.setdefault("settings", {})["pipeline"] = "custom"
    data["custom_steps"]  = steps
    data["custom_config"] = state.get("custom_config")

    # Evidenza profilo KB skill-inject nel report: se il run l'ha usata, ricostruisco
    # la KB (build_kb è deterministico e veloce: legge i JSON locali) e la allego a
    # results.json — così report.md/html mostrano attivazione, conteggi e contenuto.
    _src = (state.get("custom_config") or {}).get("source") or {}
    _use_kb = bool(_src.get("use_skill_inject_kb"))
    if _use_kb:
        try:
            from agents.red_kb import build_kb
            _kb = build_kb(BASE / "skill-inject")
            data["red_kb"] = {
                "active":          True,
                "catalog":         "catalog_paper.json",
                "classes":         {c: len(v) for c, v in sorted(_kb.items())},
                "total_exemplars": sum(len(v) for v in _kb.values()),
                "exemplars":       {c: v for c, v in sorted(_kb.items())},
            }
        except Exception as e:
            cli.warn(f"[custom/report] KB info non allegata: {e}")

    # System prompt del Red (fisso per il run) → mostrato una volta in alto nel report.
    # Ricostruito dal catalog effettivo (paper se KB attiva, altrimenti quello nostro).
    if any(r.get("red_user_prompt") for r in injections):
        try:
            from agents.red_agent import load_catalog, _system_prompt
            from agents.prompt_registry import resolve
            _catname = "catalog_paper.json" if _use_kb else "catalog.json"
            # resolve → riflette un eventuale override del Red dalla UI (come nell'agente)
            data["red_system_prompt"] = resolve(
                "red", _system_prompt(load_catalog(BASE / "config" / _catname)))
        except Exception as e:
            cli.warn(f"[custom/report] system prompt non allegato: {e}")

    (output_dir / "results.json").write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    md, html, pdf = (output_dir / f"report.{ext}" for ext in ("md", "html", "pdf"))
    _write_report(data, md)
    _write_pdf(data, pdf)
    _write_html(data, html)
    cli.phase_done(timed=False)

    # "detected" è il conteggio del Blue: senza di lui nella difesa è uno zero
    # per costruzione, e la riga di chiusura mostra invece i motori che hanno
    # girato davvero (i loro numeri stanno in engine_summary, nel report).
    _es = data.get("engine_summary") or {}
    _detected = (data.get("detected", 0) if data.get("detection_rate") is not None
                 else " / ".join(f"{k} {v['flagged']}/{v['n']}" for k, v in _es.items()) or "n/a")
    cli.footer(report_path=html, total=data.get("total", 0),
               detected=_detected,
               asr_pre=f"{data.get('asr_pre_bypasses', 0)}/{data.get('asr_pre_attempts', 0)}",
               asr_post=f"{data.get('asr_post_bypasses', 0)}/{data.get('asr_post_attempts', 0)}",
               rows=None, tokens=data.get("token_usage"))
    try:
        import core.token_tracker as token_tracker
        token_tracker.emit_now()
    except Exception:
        pass
    return {"report_data": data}


# ── Entry point ────────────────────────────────────────────────────────

def run(state: SSE3State) -> SSE3State:
    """Esegue la pipeline custom secondo state['custom_config'] (PipelineConfig.to_dict)."""
    cfg = PipelineConfig.from_dict(state.get("custom_config") or {})
    validate_or_raise(cfg)   # gate duro: niente esecuzione fuori dalla matrice

    st: dict = dict(state)
    skipped: dict = {}
    # I motori di difesa vivono nel preset (cfg.defense.engines), così un preset
    # custom salvato dalla WebUI se li porta dietro. I flag CLI --defense/--with-*
    # (globali a tutte le pipeline, in state["run_*"]) sono ADDITIVI: possono
    # abilitare un motore che il preset non prevede, mai disabilitarne uno che il
    # preset richiede.
    engines = list(cfg.defense.engines)
    for _flag, _eng in (("run_blue",         "blue"),
                        ("run_skillspector", "skillspector"),
                        ("run_cisco",        "cisco"),
                        ("run_aig",          "aig"),
                        ("run_skill_vetter", "skill_vetter"),
                        ("run_snyk",         "snyk"),
                        ("run_skills_sh",    "skills_sh")):
        if state.get(_flag) and _eng not in engines:
            engines.append(_eng)
    engines = clean_engines(engines)

    # Stesso principio additivo di "engines": il preset porta il proprio
    # defense.no_llm, i flag CLI --skillspector-no-llm/--cisco-no-llm possono
    # solo AGGIUNGERE un motore alla lista solo-statico, mai toglierlo.
    no_llm = list(cfg.defense.no_llm)
    for _flag, _eng in (("skillspector_no_llm", "skillspector"),
                        ("cisco_no_llm",        "cisco")):
        if state.get(_flag) and _eng not in no_llm:
            no_llm.append(_eng)
    no_llm = clean_no_llm(no_llm)

    # I nodi dei motori si guardano da soli su questi campi di stato (stesso
    # schema delle altre pipeline) — li allineiamo alla selezione effettiva.
    st["defense_engines"]  = engines
    st["run_blue"]         = "blue"         in engines
    st["run_skillspector"] = "skillspector" in engines
    st["run_cisco"]        = "cisco"        in engines
    st["run_aig"]          = "aig"          in engines
    st["run_skill_vetter"] = "skill_vetter" in engines
    st["run_snyk"]         = "snyk"         in engines
    st["run_skills_sh"]    = "skills_sh"    in engines
    st["skillspector_no_llm"] = "skillspector" in no_llm
    st["cisco_no_llm"]        = "cisco"        in no_llm

    steps = {"source": cfg.source.type,
             "defense": engines,
             # Chiavi per-motore mantenute accanto a "defense" per il riepilogo
             # step del report, che le legge una per una.
             "blue": "blue" in engines, "snyk": "snyk" in engines,
             "skillspector": "skillspector" in engines, "cisco": "cisco" in engines,
             "aig": "aig" in engines,
             "skill_vetter": "skill_vetter" in engines,
             "skills_sh": "skills_sh" in engines,
             "eval": cfg.eval_enabled,
             "tester": cfg.tester.enabled,
             "tester_mode": ("three-way" if "blue" in engines else "two-way") if cfg.tester.enabled else None,
             "tester_scope": cfg.tester.scope,
             "tester_injection_aware": cfg.tester.injection_aware if cfg.tester.enabled else None,
             "skipped": skipped}
    # Letto da node_tester_judge: orienta (o no) i prompt verso la sezione iniettata.
    st["tester_injection_aware"] = cfg.tester.injection_aware

    # 1) Fonte
    _merge(st, node_custom_source(st, cfg))
    if st.get("error"):
        cli.error(st["error"])
        return st

    # 2) Difesa: un nodo per motore selezionato, indipendenti fra loro.
    #    Ordine fisso (non quello in cui l'utente li ha spuntati): il Blue per
    #    primo perché dispaccia in background gli scan che non dipendono da lui
    #    (snyk/skills.sh, vedi graph.nodes.dispatch_background_scans), poi i
    #    motori LLM che condividono la sua quota, infine i due raccolti.
    _DEFENSE_NODES = (("blue", node_blue), ("skillspector", node_skillspector),
                      ("cisco", node_cisco), ("aig", node_aig),
                      ("skill_vetter", node_skill_vetter), ("snyk", node_snyk),
                      ("skills_sh", node_skills_sh))
    if engines:
        for _eng, _node in _DEFENSE_NODES:
            if _eng in engines:
                _merge(st, _node(st))
    else:
        skipped["defense"] = "no engine selected"

    # 3) Eval (optional; by construction requires blue + known ground truth)
    if cfg.eval_enabled:
        _merge(st, node_custom_eval(st))
    else:
        eval_supported = ("blue" in engines) and (
            cfg.source.type in ("red", "skill_inject")
            or (cfg.source.type == "local_preinjected"
                and find_ground_truth_json(cfg.source.local_folder_path)))
        skipped["eval"] = ("disabled in config" if eval_supported
                           else "not available for this source/defense combination")

    # 4) Tester (optional; three-way if blue, else two-way; scope all|blue_gap_only)
    if cfg.tester.enabled:
        _merge(st, _run_tester(st, cfg.tester.scope or "all"))
    else:
        skipped["tester"] = "disabled in config"

    # 5) Report (sempre)
    _merge(st, node_custom_report(st, steps))
    return st
