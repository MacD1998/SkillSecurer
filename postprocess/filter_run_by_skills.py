"""Crea una cartella "gemella" di un dataset/run filtrata su un sottoinsieme di skill.

Usato per costruire dataset_red_on_skillTrustBenchVerified_20 (e la sua sorgente
skillTrustBenchVerified_20) a partire dalle versioni complete a 26 skill: copia
solo le cartelle case_* selezionate (dataset + injected/), filtra ground_truth.json
e findings_detail sulle stesse skill, poi rigenera report.md/.pdf/.html con le
funzioni vere di benchmark.py cosi' il formato resta identico all'originale.

I contatori aggregati (total/evaluated/detected/missed/by_vuln_type/by_difficulty/
...) vengono ricalcolati da zero sul sottoinsieme filtrato, riusando la stessa
logica pura di `_compute_stats` (senza le parti che leggono stato live di processo
come cli_output/token_tracker). Le cifre non scomponibili per-skill — token usage,
costo, timing, log_events, config del run — sono lasciate identiche all'originale
(sono fatti sul run intero, non sul sottoinsieme) e annotate in run_notes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


import re as _re

_CASE_RE = _re.compile(r"case_\d+")


def _case_prefix(skill_or_filename: str) -> str:
    """Estrae 'case_00224' da qualunque punto della stringa: skill id nudo,
    nome file 'case_00224__foo__K3.md', o path a piu' livelli come
    'injected/case_00224/case_00224__foo__K3.md' o 'case_00224/SKILL.md'.
    """
    m = _CASE_RE.search(skill_or_filename)
    return m.group(0) if m else skill_or_filename


def _recompute_pure_stats(records: list[dict]) -> dict:
    """Riproduce la parte pura (senza cli_output/token_tracker) di
    benchmark._compute_stats su una lista di record filtrata.
    """
    blue_scan_failures = sum(1 for r in records if r.get("scan_failed"))
    agg = [r for r in records if not r.get("base_env_failed") and not r.get("scan_failed")]
    env_failed_count = sum(1 for r in records if r.get("base_env_failed"))
    env_setup_failures = sum(
        1 for r in records if int((r.get("env_setup") or {}).get("failed_commands") or 0) > 0
    )

    by_vuln: dict[str, dict] = {}
    by_diff: dict[str, dict] = {}
    tp = fn = 0

    for r in agg:
        if r.get("detected"): tp += 1
        else: fn += 1
        vuln_keys = r.get("blue_categories") or [r.get("vuln_type", "?")]
        for key, store in [*((vk, by_vuln) for vk in vuln_keys), (r.get("difficulty", "?"), by_diff)]:
            if key not in store:
                store[key] = {
                    "tp": 0, "fn": 0,
                    "asr_pre_cnt": 0, "asr_pre_tot": 0,
                    "asr_post_cnt": 0, "asr_post_tot": 0,
                    "executed_pre": [], "executed_post": [],
                    "inj_driven_pre": [], "inj_driven_post": [],
                    "func_preserved": [],
                    "asr_base": [], "func_base_rate": [], "func_injected_rate": [],
                    "func_fixed_rate": [], "func_deg_injected": [], "func_deg_fixed": [],
                }
            store[key]["tp" if r.get("detected") else "fn"] += 1
            if r.get("asr_pre_total"):
                store[key]["asr_pre_cnt"] += int(r.get("asr_pre_count") or 0)
                store[key]["asr_pre_tot"] += int(r.get("asr_pre_total") or 0)
            if r.get("asr_post_total"):
                store[key]["asr_post_cnt"] += int(r.get("asr_post_count") or 0)
                store[key]["asr_post_tot"] += int(r.get("asr_post_total") or 0)
            if r.get("executed_pre") is not None: store[key]["executed_pre"].append(r["executed_pre"])
            if r.get("executed_post") is not None: store[key]["executed_post"].append(r["executed_post"])
            if r.get("injection_driven_pre") is not None:
                store[key]["inj_driven_pre"].append(1 if r["injection_driven_pre"] else 0)
            if r.get("injection_driven_post") is not None:
                store[key]["inj_driven_post"].append(1 if r["injection_driven_post"] else 0)
            if r.get("functionality_preserved") is not None:
                store[key]["func_preserved"].append(1 if r["functionality_preserved"] else 0)
            if r.get("asr_base") is not None: store[key]["asr_base"].append(r["asr_base"])
            if r.get("func_base_rate") is not None: store[key]["func_base_rate"].append(r["func_base_rate"])
            if r.get("func_injected_rate") is not None: store[key]["func_injected_rate"].append(r["func_injected_rate"])
            if r.get("func_fixed_rate") is not None: store[key]["func_fixed_rate"].append(r["func_fixed_rate"])
            if r.get("func_degradation_injected") is not None: store[key]["func_deg_injected"].append(r["func_degradation_injected"])
            if r.get("func_degradation_fixed") is not None: store[key]["func_deg_fixed"].append(r["func_degradation_fixed"])

    total = tp + fn
    rate = tp / total * 100 if total else 0.0

    asr_pre_cnt = sum(int(r.get("asr_pre_count") or 0) for r in agg if r.get("asr_pre_total"))
    asr_pre_tot = sum(int(r.get("asr_pre_total") or 0) for r in agg if r.get("asr_pre_total"))
    asr_post_cnt = sum(int(r.get("asr_post_count") or 0) for r in agg if r.get("asr_post_total"))
    asr_post_tot = sum(int(r.get("asr_post_total") or 0) for r in agg if r.get("asr_post_total"))
    exec_pre_all = [r["executed_pre"] for r in agg if r.get("executed_pre") is not None]
    exec_post_all = [r["executed_post"] for r in agg if r.get("executed_post") is not None]
    inj_driven_pre = [1 if r["injection_driven_pre"] else 0 for r in agg if r.get("injection_driven_pre") is not None]
    inj_driven_post = [1 if r["injection_driven_post"] else 0 for r in agg if r.get("injection_driven_post") is not None]
    func_preserved = [1 if r["functionality_preserved"] else 0 for r in agg if r.get("functionality_preserved") is not None]
    asr_base_all = [r["asr_base"] for r in agg if r.get("asr_base") is not None]
    fb_all = [r["func_base_rate"] for r in agg if r.get("func_base_rate") is not None]
    fi_all = [r["func_injected_rate"] for r in agg if r.get("func_injected_rate") is not None]
    ff_all = [r["func_fixed_rate"] for r in agg if r.get("func_fixed_rate") is not None]
    fdi_all = [r["func_degradation_injected"] for r in agg if r.get("func_degradation_injected") is not None]
    fdf_all = [r["func_degradation_fixed"] for r in agg if r.get("func_degradation_fixed") is not None]

    pe_pre = sum(int(r.get("asr_pre_count") or 0) for r in agg if r.get("asr_post") is not None)
    pe_post = sum(int(r.get("asr_post_count") or 0) for r in agg if r.get("asr_post") is not None)
    patch_eff_pct = ((pe_pre - pe_post) / pe_pre * 100) if pe_pre else None

    def _agg_store(store):
        return {k: {
            "detected": d["tp"], "missed": d["fn"],
            "rate": round(d["tp"] / (d["tp"] + d["fn"]) * 100, 1) if (d["tp"] + d["fn"]) else 0,
            "asr_pre_rate": round(d["asr_pre_cnt"] / d["asr_pre_tot"] * 100, 1) if d["asr_pre_tot"] else None,
            "asr_post_rate": round(d["asr_post_cnt"] / d["asr_post_tot"] * 100, 1) if d["asr_post_tot"] else None,
            "executed_pre_rate": round(sum(d["executed_pre"]) / len(d["executed_pre"]) * 100, 1) if d["executed_pre"] else None,
            "executed_post_rate": round(sum(d["executed_post"]) / len(d["executed_post"]) * 100, 1) if d["executed_post"] else None,
            "inj_driven_pre_rate": round(sum(d["inj_driven_pre"]) / len(d["inj_driven_pre"]) * 100, 1) if d["inj_driven_pre"] else None,
            "inj_driven_post_rate": round(sum(d["inj_driven_post"]) / len(d["inj_driven_post"]) * 100, 1) if d["inj_driven_post"] else None,
            "func_preserved_rate": round(sum(d["func_preserved"]) / len(d["func_preserved"]) * 100, 1) if d["func_preserved"] else None,
            "asr_base_rate": round(sum(d["asr_base"]) / len(d["asr_base"]) * 100, 1) if d["asr_base"] else None,
            "func_base_rate_avg": round(sum(d["func_base_rate"]) / len(d["func_base_rate"]), 1) if d["func_base_rate"] else None,
            "func_injected_rate_avg": round(sum(d["func_injected_rate"]) / len(d["func_injected_rate"]), 1) if d["func_injected_rate"] else None,
            "func_fixed_rate_avg": round(sum(d["func_fixed_rate"]) / len(d["func_fixed_rate"]), 1) if d["func_fixed_rate"] else None,
            "func_deg_injected_avg": round(sum(d["func_deg_injected"]) / len(d["func_deg_injected"]), 1) if d["func_deg_injected"] else None,
            "func_deg_fixed_avg": round(sum(d["func_deg_fixed"]) / len(d["func_deg_fixed"]), 1) if d["func_deg_fixed"] else None,
        } for k, d in store.items()}

    return {
        "total": len(records),
        "evaluated": total,
        "env_failed_count": env_failed_count,
        "env_setup_failures": env_setup_failures,
        "blue_scan_failures": blue_scan_failures,
        "detected": tp,
        "missed": fn,
        "detection_rate_raw": round(rate, 1),
        "asr_pre_rate": round(asr_pre_cnt / asr_pre_tot * 100, 1) if asr_pre_tot else None,
        "asr_post_rate": round(asr_post_cnt / asr_post_tot * 100, 1) if asr_post_tot else None,
        "asr_pre_bypasses": asr_pre_cnt,
        "asr_pre_attempts": asr_pre_tot,
        "asr_post_bypasses": asr_post_cnt,
        "asr_post_attempts": asr_post_tot,
        "executed_pre_rate": round(sum(exec_pre_all) / len(exec_pre_all) * 100, 1) if exec_pre_all else None,
        "executed_post_rate": round(sum(exec_post_all) / len(exec_post_all) * 100, 1) if exec_post_all else None,
        "patch_effectiveness": round(patch_eff_pct, 1) if patch_eff_pct is not None else None,
        "injectable_count": pe_pre,
        "blocked_count": pe_pre - pe_post,
        "inj_driven_pre_rate": round(sum(inj_driven_pre) / len(inj_driven_pre) * 100, 1) if inj_driven_pre else None,
        "inj_driven_post_rate": round(sum(inj_driven_post) / len(inj_driven_post) * 100, 1) if inj_driven_post else None,
        "func_preserved_rate": round(sum(func_preserved) / len(func_preserved) * 100, 1) if func_preserved else None,
        "asr_base_rate": round(sum(asr_base_all) / len(asr_base_all) * 100, 1) if asr_base_all else None,
        "func_base_rate_avg": round(sum(fb_all) / len(fb_all), 1) if fb_all else None,
        "func_injected_rate_avg": round(sum(fi_all) / len(fi_all), 1) if fi_all else None,
        "func_fixed_rate_avg": round(sum(ff_all) / len(ff_all), 1) if ff_all else None,
        "func_deg_injected_avg": round(sum(fdi_all) / len(fdi_all), 1) if fdi_all else None,
        "func_deg_fixed_avg": round(sum(fdf_all) / len(fdf_all), 1) if fdf_all else None,
        "by_vuln_type": _agg_store(by_vuln),
        "by_difficulty": _agg_store(by_diff),
    }


def build_filtered_data(original: dict, case_ids: set[str]) -> dict:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from reporting.report import _blue_eval_aggregate, _engine_summary

    findings = [r for r in original.get("findings_detail", []) if _case_prefix(r.get("skill", "")) in case_ids]
    stats = _recompute_pure_stats(findings)

    state = {
        "custom_config": original.get("custom_config"),
        "defense_engines": original.get("defense_engines"),
    }
    _defense = original.get("defense_engines")
    _blue_ran = ("blue" in _defense) if _defense is not None else True

    new_data = dict(original)
    new_data.update({
        "run_notes": (
            f"Sottoinsieme filtrato a {len(case_ids)}/{len(set(_case_prefix(r.get('skill','')) for r in original.get('findings_detail', [])))} "
            f"skill del run originale ({original.get('total')} injection totali). "
            "I contatori (total/evaluated/detected/missed/by_vuln_type/by_difficulty) sono "
            "ricalcolati sul sottoinsieme. Token usage, costo, timing, log_events e "
            "configurazione restano quelli del run originale (non scomponibili per skill)."
            + (f" Nota originale: {original['run_notes']}" if original.get("run_notes") else "")
        ),
        "total": stats["total"],
        "evaluated": stats["evaluated"],
        "env_failed_count": stats["env_failed_count"],
        "env_setup_failures": stats["env_setup_failures"],
        "blue_scan_failures": stats["blue_scan_failures"],
        "detected": stats["detected"],
        "missed": stats["missed"],
        "detection_rate": stats["detection_rate_raw"] if _blue_ran else None,
        "asr_pre_rate": stats["asr_pre_rate"],
        "asr_post_rate": stats["asr_post_rate"],
        "asr_pre_bypasses": stats["asr_pre_bypasses"],
        "asr_pre_attempts": stats["asr_pre_attempts"],
        "asr_post_bypasses": stats["asr_post_bypasses"],
        "asr_post_attempts": stats["asr_post_attempts"],
        "executed_pre_rate": stats["executed_pre_rate"],
        "executed_post_rate": stats["executed_post_rate"],
        "patch_effectiveness": stats["patch_effectiveness"],
        "injectable_count": stats["injectable_count"],
        "blocked_count": stats["blocked_count"],
        "inj_driven_pre_rate": stats["inj_driven_pre_rate"],
        "inj_driven_post_rate": stats["inj_driven_post_rate"],
        "func_preserved_rate": stats["func_preserved_rate"],
        "asr_base_rate": stats["asr_base_rate"],
        "func_base_rate_avg": stats["func_base_rate_avg"],
        "func_injected_rate_avg": stats["func_injected_rate_avg"],
        "func_fixed_rate_avg": stats["func_fixed_rate_avg"],
        "func_deg_injected_avg": stats["func_deg_injected_avg"],
        "func_deg_fixed_avg": stats["func_deg_fixed_avg"],
        "by_vuln_type": stats["by_vuln_type"],
        "by_difficulty": stats["by_difficulty"],
        "blue_eval": _blue_eval_aggregate(findings, state),
        "engine_summary": _engine_summary(findings, state),
        "findings_detail": findings,
    })
    return new_data


def generate(src_run_dir: Path, dst_run_dir: Path, case_ids: list[str], *,
             src_dataset_dir: Path, dst_dataset_name: str) -> dict:
    """Copia src_run_dir -> dst_run_dir filtrando su case_ids (skill), rigenerando
    injected/, _custom_config.json, results.json e i report."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from reporting.report import _write_report, _write_pdf, _write_html

    case_set = set(case_ids)
    dst_run_dir.mkdir(parents=True, exist_ok=True)

    # ── injected/ ────────────────────────────────────────────────────
    src_injected = src_run_dir / "injected"
    dst_injected = dst_run_dir / "injected"
    if dst_injected.exists():
        shutil.rmtree(dst_injected)
    dst_injected.mkdir(parents=True)
    for case_dir in sorted(src_injected.iterdir()):
        if case_dir.is_dir() and case_dir.name in case_set:
            shutil.copytree(case_dir, dst_injected / case_dir.name)
    gt_path = src_injected / "ground_truth.json"
    if gt_path.is_file():
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        gt_filtered = {k: v for k, v in gt.items() if _case_prefix(k) in case_set}
        (dst_injected / "ground_truth.json").write_text(
            json.dumps(gt_filtered, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── _custom_config.json ─────────────────────────────────────────
    cfg_path = src_run_dir / "_custom_config.json"
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        src = cfg.get("source") or {}
        if "selected_files" in src:
            src["selected_files"] = [f for f in src["selected_files"] if _case_prefix(f) in case_set]
        if "local_folder_path" in src:
            src["local_folder_path"] = str(Path(src["local_folder_path"]).parent / dst_dataset_name)
        (dst_run_dir / "_custom_config.json").write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── results.json + report.md/.pdf/.html ─────────────────────────
    original = json.loads((src_run_dir / "results.json").read_text(encoding="utf-8"))
    new_data = build_filtered_data(original, case_set)

    (dst_run_dir / "results.json").write_text(
        json.dumps(new_data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    _write_report(new_data, dst_run_dir / "report.md")
    _write_pdf(new_data, dst_run_dir / "report.pdf")
    _write_html(new_data, dst_run_dir / "report.html")

    return {
        "dst_run_dir": str(dst_run_dir),
        "n_cases": len(case_set),
        "n_findings": len(new_data["findings_detail"]),
        "files": sorted(p.name for p in dst_run_dir.iterdir() if p.is_file()),
    }


def generate_defense_eval(src_run_dir: Path, dst_run_dir: Path, case_ids: list[str], *,
                           artifact_subdir: str = "fixed",
                           rewrite_local_folder_path: Path | None = None) -> dict:
    """Variante di `generate` per run che consumano un dataset pre-iniettato
    (source.type == "local_preinjected", es. table6_sonnet_redinj_*): l'unica
    cartella con artefatti locali da filtrare e' `artifact_subdir` (default
    "fixed", una sotto-cartella per injection con lo SKILL.md patchato), non
    c'e' ground_truth.json locale (vive nel dataset upstream referenziato da
    source.local_folder_path). Se `rewrite_local_folder_path` e' passato,
    aggiorna quel riferimento a puntare al twin filtrato del dataset upstream.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from reporting.report import _write_report, _write_pdf, _write_html

    case_set = set(case_ids)
    dst_run_dir.mkdir(parents=True, exist_ok=True)

    # ── artifact_subdir (es. fixed/) ────────────────────────────────
    src_artifacts = src_run_dir / artifact_subdir
    dst_artifacts = dst_run_dir / artifact_subdir
    if dst_artifacts.exists():
        shutil.rmtree(dst_artifacts)
    if src_artifacts.is_dir():
        dst_artifacts.mkdir(parents=True)
        for entry in sorted(src_artifacts.iterdir()):
            if _case_prefix(entry.name) in case_set:
                if entry.is_dir():
                    shutil.copytree(entry, dst_artifacts / entry.name)
                else:
                    shutil.copy2(entry, dst_artifacts / entry.name)

    # ── _custom_config.json ─────────────────────────────────────────
    cfg_path = src_run_dir / "_custom_config.json"
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        src = cfg.get("source") or {}
        if "selected_files" in src:
            src["selected_files"] = [f for f in src["selected_files"] if _case_prefix(f) in case_set]
        if rewrite_local_folder_path is not None and "local_folder_path" in src:
            src["local_folder_path"] = str(rewrite_local_folder_path)
        (dst_run_dir / "_custom_config.json").write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── results.json + report.md/.pdf/.html ─────────────────────────
    original = json.loads((src_run_dir / "results.json").read_text(encoding="utf-8"))
    new_data = build_filtered_data(original, case_set)

    (dst_run_dir / "results.json").write_text(
        json.dumps(new_data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    _write_report(new_data, dst_run_dir / "report.md")
    _write_pdf(new_data, dst_run_dir / "report.pdf")
    _write_html(new_data, dst_run_dir / "report.html")

    return {
        "dst_run_dir": str(dst_run_dir),
        "n_cases": len(case_set),
        "n_findings": len(new_data["findings_detail"]),
        "n_artifacts": sum(1 for p in dst_artifacts.iterdir()) if dst_artifacts.is_dir() else 0,
        "files": sorted(p.name for p in dst_run_dir.iterdir() if p.is_file()),
    }
