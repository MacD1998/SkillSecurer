"""
run_index.py — scopre le run in results/ e le raggruppa per dataset di input.
=============================================================================
Due run sono confrontabili quando hanno scansionato ESATTAMENTE gli stessi file
di input. La chiave di join per caso (`case_key`) è:

  • il tratto di path dopo l'ultimo `/injected/` quando presente — le run su
    dataset iniettati copiano l'input nella propria cartella di run
    (`results/<run>/injected/<inj_dir>/SKILL.md`), quindi il path assoluto
    cambia da run a run ma la coda no;
  • altrimenti il path assoluto (`inj_path`), che per i dataset condivisi
    (skills_sh_dataset/, skillTrustBenchVerified/, …) è già identico;
  • in ultima istanza il nome della skill.

Il "fingerprint" di un dataset è l'hash dell'insieme ordinato delle case key:
run con lo stesso fingerprint hanno visto gli stessi file e solo quelle vengono
proposte insieme nella UI di post-processing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE / "results"


def case_key(rec: dict) -> str:
    """Identità del caso, stabile fra run diverse sullo stesso dataset."""
    p = (rec.get("inj_path") or "").replace("\\", "/")
    if "/injected/" in p:
        return p.rsplit("/injected/", 1)[1]
    if p:
        return p
    return rec.get("skill") or ""


def _fingerprint(keys) -> str:
    h = hashlib.sha1()
    for k in sorted(keys):
        h.update(k.encode("utf-8", "replace"))
        h.update(b"\0")
    return h.hexdigest()[:16]


def _engines_of(data: dict, fd: list) -> list[str]:
    """Motori presenti nella run: `defense_engines` quando c'è, altrimenti
    dedotti dai record (le run vecchie non lo persistono)."""
    engs = [e for e in (data.get("defense_engines") or []) if e]
    if engs:
        return engs
    seen: list[str] = []
    for r in fd:
        for e in (r.get("engines") or {}):
            if e not in seen:
                seen.append(e)
    return seen


def scan_run(run_dir: Path) -> dict | None:
    """Metadati di una run, o None se non è una run comparabile (niente
    results.json leggibile, o nessun motore/caso con `engines` popolato)."""
    jf = run_dir / "results.json"
    if not jf.is_file():
        return None
    try:
        data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    fd = data.get("findings_detail") or []
    keys = [case_key(r) for r in fd]
    keys = [k for k in keys if k]
    engines = _engines_of(data, fd)
    if not keys or not engines:
        # Run legacy senza il blocco `engines` per record: non joinabile con
        # il modello per-motore usato dal confronto.
        return None
    return {
        "run_id":      run_dir.name,
        "path":        str(run_dir),
        "timestamp":   data.get("timestamp"),
        "started_at":  data.get("started_at"),
        "model":       data.get("model"),
        "notes":       data.get("run_notes"),
        "engines":     engines,
        "n_cases":     len(keys),
        "fingerprint": _fingerprint(keys),
        "detection_rate": data.get("detection_rate"),
    }


def list_runs(results_dir: Path | str | None = None) -> list[dict]:
    d = Path(results_dir) if results_dir else RESULTS_DIR
    out = []
    # results/ (run vere) + results/examples/ (esempi curati a mano, tenuti in
    # git — vedi .gitignore: `results/*` ignorato TRANNE `results/examples/`).
    # Un livello in più, quindi uno scan non ricorsivo di `d` da solo non li
    # vede — stesso bug/fix di webui/app.py::_scan_run_dirs per la History.
    for container in (d, d / "examples"):
        if not container.is_dir():
            continue
        for sub in sorted(container.iterdir()):
            if not sub.is_dir():
                continue
            entry = scan_run(sub)
            if entry:
                out.append(entry)
    out.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return out


def group_by_dataset(results_dir: Path | str | None = None) -> list[dict]:
    """Run raggruppate per fingerprint del dataset di input.

    Restituisce i gruppi con >= 2 run per primi (gli unici confrontabili fra
    run diverse); i gruppi singoli restano in coda perché una singola run con
    più motori (es. blue + skills_sh) è comunque confrontabile da sola.
    """
    groups: dict[str, dict] = {}
    for r in list_runs(results_dir):
        g = groups.setdefault(r["fingerprint"], {
            "fingerprint": r["fingerprint"],
            "n_cases": r["n_cases"],
            "runs": [],
        })
        g["runs"].append(r)
    out = list(groups.values())
    for g in out:
        engines: list[str] = []
        for r in g["runs"]:
            for e in r["engines"]:
                if e not in engines:
                    engines.append(e)
        g["engines"] = engines
        g["n_runs"] = len(g["runs"])
        # Etichetta leggibile: prefisso comune dei run_id, altrimenti il più recente.
        names = [r["run_id"] for r in g["runs"]]
        g["label"] = _common_label(names)
        g["latest"] = max((r.get("timestamp") or "") for r in g["runs"])
    out.sort(key=lambda g: (-g["n_runs"], g["latest"]), reverse=False)
    out.sort(key=lambda g: (g["n_runs"] > 1, g["latest"]), reverse=True)
    return out


def _common_label(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    prefix = names[0]
    for n in names[1:]:
        while prefix and not n.startswith(prefix):
            prefix = prefix[:-1]
    prefix = prefix.rstrip("_-")
    # Prefisso troppo corto = run senza famiglia comune: meglio nominare la
    # prima run e contare le altre che mostrare un moncone ("webui_run…").
    if len(prefix) < 12:
        return f"{sorted(names)[0]} +{len(names) - 1}"
    return prefix


if __name__ == "__main__":
    for g in group_by_dataset():
        print(f"[{g['fingerprint']}] {g['n_cases']:5d} casi · {g['n_runs']:2d} run · "
              f"{g['label']}  engines={g['engines']}")
        for r in g["runs"]:
            print(f"    - {r['run_id']:60s} {r['engines']}")
