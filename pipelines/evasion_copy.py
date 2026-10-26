"""
Pipeline: Evasion copy
======================
Prende una run precedente in cui è girato SOLO il Red (nessuna difesa/eval/tester) e
ne crea una copia identica — stesse skill base, stessi payload di vuln_type, stessa
config — in cui ogni file iniettato contiene anche una seconda injection: il testo di
LLM evasion rivolto allo scanner (vedi config/evasion.json). Serve a ottenere un secondo
risultato "a parità di tutto il resto" dove l'unica differenza è l'evasion aggiunta dal
Red, da confrontare con la run originale.

    source run ──► (per ogni file iniettato) Red: add_evasion ──► run copia ──► report

La run copia ha lo stesso layout di una run Red (`injected/<skill>/<file>.md`,
`injected/ground_truth.json`, `_custom_config.json`, `results.json`, report), quindi si
usa come qualunque dataset pre-iniettato (custom → local_preinjected). I nomi dei file
sono invariati: nel post-processing i casi dei due dataset si accoppiano per chiave.

Ground truth: `injection` resta il solo payload di vuln_type; l'evasion è nei campi
`evasion`/`evasion_technique`, così l'eval non la scambia per l'attacco.

Questo modulo è volutamente leggero all'import (solo stdlib + cli_output): la WebUI usa
`inspect_run` per elencare le run idonee senza caricare LangGraph. Gli import pesanti
sono dentro `run`.
"""
from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import core.cli_output as cli

BASE = Path(__file__).resolve().parent.parent


# ── Ispezione della run sorgente ───────────────────────────────────────

def _injected_tail(p: str) -> str | None:
    """Il tratto di path dopo l'ultimo `/injected/` (stessa regola di
    postprocess.run_index.case_key): il path assoluto cambia da una macchina/run
    all'altra, la coda no."""
    p = (p or "").replace("\\", "/")
    return p.rsplit("/injected/", 1)[1] if "/injected/" in p else None


def locate_injected(rec: dict, run_dir: Path) -> Path | None:
    """File iniettato di un record. `inj_path` in results.json è assoluto e punta
    spesso alla macchina dove la run è stata prodotta (non esiste qui): in quel caso
    si ricostruisce dentro la cartella della run, dove vive la copia del dataset."""
    inj = rec.get("inj_path") or ""
    cands: list[Path] = []
    if inj:
        cands.append(Path(inj))
    tail = _injected_tail(inj)
    if tail:
        cands.append(run_dir / "injected" / tail)
    if inj:
        cands.append(run_dir / "injected" / str(rec.get("skill") or "") / Path(inj).name)
    return next((c for c in cands if c.is_file()), None)


def is_red_only(data: dict) -> bool:
    """True se in questa run è girato solo il Red: pipeline `red-only`, oppure custom
    con fonte red e nessuna difesa/eval/tester. Con una difesa o un tester i record
    portano finding/ASR calcolati sui file ORIGINALI: copiarli su file modificati
    darebbe una run incoerente."""
    if (data.get("settings") or {}).get("pipeline") == "red-only":
        return True
    steps = data.get("custom_steps") or {}
    return (steps.get("source") == "red" and not steps.get("defense")
            and not steps.get("eval") and not steps.get("tester"))


def inspect_run(run_dir: Path) -> dict:
    """Idoneità di `run_dir` come sorgente. Ritorna sempre un dict:
    {ok, reason, n, skills, vuln_types, difficulties, has_evasion, missing}. `reason`
    spiega il rifiuto quando ok=False."""
    out = {"ok": False, "reason": None, "n": 0, "skills": 0, "vuln_types": [],
           "difficulties": [], "has_evasion": False, "missing": 0}
    jf = Path(run_dir) / "results.json"
    if not jf.is_file():
        out["reason"] = "no results.json"
        return out
    try:
        data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:
        out["reason"] = f"results.json unreadable: {e}"
        return out
    recs = [r for r in (data.get("findings_detail") or []) if isinstance(r, dict)]
    out["n"]            = len(recs)
    out["skills"]       = len({r.get("skill") for r in recs})
    out["vuln_types"]   = sorted({r["vuln_type"] for r in recs if r.get("vuln_type")})
    out["difficulties"] = sorted({r["difficulty"] for r in recs if r.get("difficulty")})
    out["has_evasion"]  = any(r.get("evasion_text") for r in recs)
    if not recs:
        out["reason"] = "no injections in results.json"
    elif not is_red_only(data):
        out["reason"] = "not a Red-only run (a defense, eval or tester ran on it)"
    elif out["has_evasion"]:
        out["reason"] = "already contains LLM-evasion injections"
    elif not all((r.get("inj_text") or "").strip() for r in recs):
        out["reason"] = "records without injection text"
    else:
        out["missing"] = sum(1 for r in recs if locate_injected(r, Path(run_dir)) is None)
        if out["missing"] == len(recs):
            out["reason"] = "injected files not found (expected under <run>/injected/)"
        else:
            out["ok"] = True
    return out


def resolve_run_dir(arg: str) -> Path:
    """`--source-run`: path assoluto, relativo alla root del progetto, o nome di una
    run sotto results/ (anche results/examples/)."""
    p = Path(arg)
    cands = [p, BASE / p, BASE / "results" / p, BASE / "results" / "examples" / p]
    for c in cands:
        if (c / "results.json").is_file():
            return c.resolve()
    raise FileNotFoundError(f"source run not found (no results.json): {arg}")


# ── Esecuzione ─────────────────────────────────────────────────────────

def _rel_in_injected(rec: dict, src_dir: Path) -> Path:
    """Path relativo del file dentro `injected/`, identico a quello della sorgente
    così i casi dei due dataset si accoppiano per chiave."""
    tail = _injected_tail(rec.get("inj_path") or "")
    if tail:
        return Path(tail)
    return Path(str(rec.get("skill") or "")) / Path(rec["inj_path"]).name


def _copy_config(src_dir: Path, data: dict, techniques: list[str] | None,
                 out_name: str) -> dict:
    """Config della copia = quella della sorgente, con evasion attiva. Se la sorgente
    non ha una config (run `red-only` da CLI) se ne costruisce una minima."""
    cfg = data.get("custom_config")
    cf  = src_dir / "_custom_config.json"
    if not cfg and cf.is_file():
        try:
            cfg = json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            cfg = None
    cfg = json.loads(json.dumps(cfg)) if cfg else {"name": out_name,
                                                   "source": {"type": "red"},
                                                   "defense": {"engines": [], "no_llm": []},
                                                   "eval": False,
                                                   "tester": {"enabled": False, "scope": None,
                                                              "injection_aware": True}}
    cfg["name"] = out_name
    cfg.setdefault("source", {"type": "red"})
    cfg["source"]["red_evasion"]            = True
    cfg["source"]["red_evasion_techniques"] = techniques or None
    return cfg


def run(state: dict) -> dict:
    """state: source_run_dir (Path), output_dir (Path), parallel, red_evasion_techniques,
    notes, input_price, output_price."""
    from agents.red_agent import add_evasion, load_evasion
    from pipelines.custom import node_custom_report

    src_dir = Path(state["source_run_dir"]).resolve()
    out_dir = Path(state["output_dir"]).resolve()
    parallel   = max(1, int(state.get("parallel") or 4))
    techniques = state.get("red_evasion_techniques") or None

    def _fail(msg: str) -> dict:
        cli.error(msg)
        return {**state, "error": msg}

    if out_dir == src_dir:
        return _fail("output folder must differ from the source run (the copy never overwrites it)")
    if (out_dir / "results.json").exists():
        return _fail(f"output folder already holds a run: {out_dir} — pick a new one")

    info = inspect_run(src_dir)
    if not info["ok"]:
        return _fail(f"source run '{src_dir.name}' not usable: {info['reason']}")
    try:
        evasion = load_evasion(techniques)
    except ValueError as e:
        return _fail(str(e))

    data = json.loads((src_dir / "results.json").read_text(encoding="utf-8", errors="ignore"))
    # Ordine deterministico → assegnazione round-robin delle tecniche riproducibile.
    recs = sorted((r for r in data["findings_detail"] if isinstance(r, dict)),
                  key=lambda r: (str(r.get("skill")), str(r.get("vuln_type")),
                                 str(r.get("difficulty"))))
    # max_files: cap sul numero di injection della sorgente da augmentare (le prime, in
    # ordine skill → vuln_type → difficulty: le skill si completano una alla volta).
    n_source_all = len(recs)
    mf = state.get("max_files")
    if mf and int(mf) < len(recs):
        recs = recs[:int(mf)]
    n_tech = len(evasion["techniques"])

    cli.start_run()
    cli.header(scope=f"evasion copy of {src_dir.name}", injections=len(recs), attempts="n/a",
               parallel=parallel, vuln_types=[])
    cli.phase("red", f"adding LLM evasion to {len(recs)} injected skills")
    if info["missing"]:
        cli.warn(f"{info['missing']} injected file(s) not found in the source run — skipped")

    inj_dir  = out_dir / "injected"
    lock     = threading.Lock()
    done     = [0]
    skipped: list[dict] = []

    def process(idx_rec):
        idx, rec = idx_rec
        label = f"{rec.get('skill')} {rec.get('vuln_type')}/{rec.get('difficulty')}"
        try:
            src_file = locate_injected(rec, src_dir)
            if src_file is None:
                raise FileNotFoundError("injected file not found")
            content = src_file.read_text(encoding="utf-8", errors="ignore")
            payload = rec["inj_text"]
            # Il payload deve esserci davvero: l'evasion gli si dispone attorno e la
            # sua posizione (line_num) è quella registrata dal Red.
            if payload.strip() not in content:
                raise ValueError("recorded payload not found in the injected file")
            ev = add_evasion(str(rec.get("skill")), content, payload,
                             int(rec.get("line_num") or 1),
                             evasion["techniques"][idx % n_tech], evasion)
            rel = _rel_in_injected(rec, src_dir)
            dst = inj_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(ev["content"], encoding="utf-8")
        except Exception as e:
            with lock:
                done[0] += 1
                skipped.append({"skill": rec.get("skill"), "vuln_type": rec.get("vuln_type"),
                                "difficulty": rec.get("difficulty"), "reason": str(e)})
                cli.warn(f"[evasion] {label}: {e} — skipped")
                cli.item(f"{done[0]}/{len(recs)} {label} (skip)")
            return None
        new = dict(rec)
        new.update({
            "inj_path":            str(dst),
            "line_num":            ev["payload_line_num"],
            "evasion_text":        ev["evasion_text"],
            "evasion_technique":   ev["evasion_technique"],
            "evasion_line_num":    ev["evasion_line_num"],
            "evasion_reasoning":   ev["reasoning"],
            "evasion_user_prompt": ev["user_prompt"],
            "evasion_source_run":  src_dir.name,
        })
        with lock:
            done[0] += 1
            cli.item(f"{done[0]}/{len(recs)} {label} ✓ {ev['evasion_technique']}")
        return new

    new_recs: list[dict] = []
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        for fut in as_completed([ex.submit(process, ir) for ir in enumerate(recs)]):
            r = fut.result()
            if r:
                new_recs.append(r)
    cli.phase_done()
    if not new_recs:
        return _fail("no injection could be augmented with an evasion — nothing written")

    new_recs.sort(key=lambda r: (str(r.get("skill")), str(r.get("vuln_type")),
                                 str(r.get("difficulty"))))

    # ground_truth.json (stessa forma di graph.nodes._ground_truth_entry): rende la
    # cartella riusabile come dataset pre-iniettato con eval.
    from graph.nodes import _ground_truth_entry
    (inj_dir / "ground_truth.json").write_text(
        json.dumps({Path(r["inj_path"]).name: _ground_truth_entry(r) for r in new_recs},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    cfg = _copy_config(src_dir, data, techniques, out_dir.name)
    (out_dir / "_custom_config.json").write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    note = (f"LLM-evasion copy of run '{src_dir.name}': same base skills and vuln_type "
            f"payloads, plus one evasion injection per file "
            f"({len(new_recs)}/{len(recs)} augmented"
            + (f", capped from {n_source_all} by max files" if len(recs) < n_source_all else "")
            + ").")
    if state.get("notes"):
        note += f" {state['notes']}"

    steps = dict(data.get("custom_steps") or {"source": "red", "defense": [], "eval": False,
                                              "tester": False})
    steps["evasion_copy"] = {
        "source_run": src_dir.name,
        "techniques": [t["id"] for t in evasion["techniques"]],
        "n_source":   n_source_all,
        "n_augmented": len(new_recs),
        "skipped":    skipped,
    }

    st = {**state,
          "output_dir":       out_dir,
          "injections":       new_recs,
          # node_custom_report/_compute_stats leggono solo i NOMI delle skill da qui.
          "skill_contents":   {r["skill"]: "" for r in new_recs},
          "custom_config":    cfg,
          "defense_engines":  [],
          "notes":            note}
    st.update(node_custom_report(st, steps))
    return st
