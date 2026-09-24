"""
SSE3State — stato condiviso tra tutti i nodi LangGraph
=======================================================
Lo stato è un TypedDict che fluisce attraverso il grafo.
Ogni nodo legge dallo stato e restituisce un dict con i campi aggiornati.
LangGraph fa il merge automatico (shallow merge sui campi restituiti).

Convenzione: ogni nodo restituisce SOLO i campi che ha modificato,
non l'intero stato — LangGraph fa il merge.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from typing_extensions import TypedDict


# ── Record per singola injection ──────────────────────────────────────
# Creato dal nodo Red, arricchito da Blue, Tester, Judge.
# Tutti i campi sono opzionali (total=False) perché vengono popolati
# progressivamente dalle fasi.

class InjectionRecord(TypedDict, total=False):
    # ── Identità (Red) ────────────────────────────────────────────────
    skill:          str
    vuln_type:      str
    blue_categories: list[str]   # blue-only (no ground truth): TUTTE le macro-categorie Blue trovate, non solo la più severa (vuln_type)
    difficulty:     str
    diff_label:     str
    strategy:       str
    line_num:       int
    inj_text:       str
    reasoning:      str
    inj_path:       str        # path assoluto al SKILL.md iniettato
    base_skill_path: str       # path alla BASE pulita (blue-eval-testing: SKILL.md sorgente)
    popularity_rank: Optional[int]  # posizione nell'ordine di popolarità skills_sh_dataset
                                     # (node_load_external_skills, via _popularity_rank) —
                                     # None per fonti senza nozione di popolarità (red/skill_inject/
                                     # online). Riusato dai sort post-parallelo per non perdere
                                     # l'ordinamento in output (report/third-party comparison).

    # ── Verdetti per motore di difesa (forma uniforme) ────────────────
    # {"blue"|"skillspector"|"cisco"|"snyk"|"skills_sh":
    #     {"flagged": bool, "findings": list[dict], "scan_error": str|None,
    #      "available": bool, "patched": bool, "meta": dict}}
    # Popolato da graph.nodes._with_engine, un motore per nodo eseguito. È la
    # forma su cui lavora il confronto post-hoc fra run diverse; i campi piatti
    # qui sotto restano scritti in parallelo per report/analytics già esistenti
    # e per le run salvate prima di questo campo.
    engines:                Optional[dict]

    # ── Blue ──────────────────────────────────────────────────────────
    detected:               bool
    confidence:             float
    findings:               list[dict]
    scan_failed:            Optional[bool]  # True se lo scan è fallito (≠ skill pulita)
    scan_error:             Optional[str]   # motivo dello scan fallito
    scan_reasoning:         Optional[str]   # ragionamento testuale del Blue (anche se findings=[])
    patch_reasoning:        Optional[str]
    patches_applied:        Optional[list[dict]]
    fix_path:               Optional[str]   # path al SKILL.md fixato
    skill_content_injected: Optional[str]
    skill_content_fixed:    Optional[str]

    # ── Snyk (confronto opzionale, --with-snyk) ────────────────────────
    snyk_findings:           Optional[list[dict]]  # finding normalizzati snyk-agent-scan
    snyk_scan_error:         Optional[str]         # motivo del fallimento, se presente
    snyk_source:             Optional[str]         # "live" | "skills_sh_audit"

    # ── SkillSpector (confronto opzionale, --with-skillspector) ────────
    skillspector_findings:   Optional[list[dict]]  # finding normalizzati NVIDIA SkillSpector
    skillspector_scan_error: Optional[str]
    skillspector_used_llm:   Optional[bool]  # False = solo analisi statica (no credenziali LLM)

    # ── Cisco skill-scanner (confronto opzionale, --with-cisco) ────────
    cisco_findings:   Optional[list[dict]]  # finding normalizzati Cisco skill-scanner
    cisco_scan_error: Optional[str]
    cisco_used_llm:   Optional[bool]  # False = solo analisi statica (no credenziali LLM)

    # ── skills.sh (confronto opzionale, verdetto già calcolato) ─────────
    skills_sh_available:   Optional[bool]  # False = skill fuori dal dataset skills_sh_dataset
    skills_sh_engines:      Optional[dict]  # {"snyk"|"socket"|"agentTrustHub": {flagged, findings}}
    skills_sh_any_flagged:  Optional[bool]  # OR sui motori disponibili

    # ── Tester + Judge PRE-patch ──────────────────────────────────────
    asr_pre:              Optional[float]  # rate continuo: bypass attempts / attempts
    asr_pre_count:        Optional[int]    # attempt che hanno eseguito l'injection
    asr_pre_total:        Optional[int]    # attempt effettivamente eseguiti (non-skip)
    executed_pre:         Optional[int]   # 0/1 — confermata dal judge
    injection_driven_pre: Optional[bool]  # guidata dalla skill o dal prompt
    utility_pre:          Optional[bool]  # task legittimo completato pre-patch
    evidence_pre:         str             # riga esatta del log come prova
    bypass_prompt_pre:    str             # prompt che ha causato il bypass
    bypass_attempt_pre:   Optional[int]   # numero del tentativo
    attempts_pre:         list[dict]      # tutti i tentativi con tool_calls

    # ── Tester + Judge POST-patch ─────────────────────────────────────
    asr_post:               Optional[float]  # rate continuo: bypass attempts / attempts
    asr_post_count:         Optional[int]
    asr_post_total:         Optional[int]
    executed_post:          Optional[int]
    injection_driven_post:  Optional[bool]
    utility_post:           Optional[bool]
    evidence_post:          str
    bypass_prompt_post:     str
    bypass_attempt_post:    Optional[int]
    attempts_post:          list[dict]

    # ── Metriche derivate ─────────────────────────────────────────────
    patch_eff:                   Optional[float]  # asr_pre - asr_post (rate continui)
    functionality_preserved:     Optional[bool]
    functionality_test_results:  list[dict]

    # ── Tester three-way metrics (BASE / INJECTED / FIXED) ────────────
    # Calcolate da node_tester_judge a partire da _tester_three_way.
    asr_base:                    Optional[int]    # 0/1 — atteso 0 (sanity check)
    func_base_rate:              Optional[float]  # % prompt che completano task su BASE
    func_injected_rate:          Optional[float]  # idem su INJECTED
    func_fixed_rate:             Optional[float]  # idem su FIXED
    func_degradation_injected:   Optional[float]  # base - injected (positivo = funz persa)
    func_degradation_fixed:      Optional[float]  # base - fixed

    # ── FIXED run saltata ─────────────────────────────────────────────
    fixed_skipped:               Optional[bool]   # True se la FIXED non è stata eseguita
    fixed_skip_reason:           Optional[str]    # "fixed" | "identical_to_base"

    # ── BASE environment failure ──────────────────────────────────────
    base_env_failed:             Optional[bool]   # True se TUTTI i prompt falliti sulla BASE
    skipped_base_count:          Optional[int]    # quanti prompt falliti sulla BASE (parziale)

    # ── EnvironmentAgent ──────────────────────────────────────────────
    env_setup:                   Optional[dict]   # {created, notes, setup_commands, ...}


# ── Stato globale del grafo ───────────────────────────────────────────

class SSE3State(TypedDict, total=False):

    # ── Configurazione input ──────────────────────────────────────────
    # Impostata dal pipeline prima di invocare il grafo.
    skills_dir:        Path
    skill_names:       list[str]
    output_dir:        Path
    catalog_path:      Path
    parallel:          int
    max_files:         Optional[int]
    max_attempts:      int           # numero di prompt replayati su BASE/INJECTED/FIXED
    docker_image:      str
    difficulties:      Optional[list[str]]   # es. ["K3"] — None = tutte
    vuln_types:        Optional[list[str]]   # es. ["data_exfiltration"] — None = tutte
    notes:             Optional[str]         # nota libera sul test (mostrata nel report)
    input_price:       Optional[float]       # costo per 1M token input (None = no stima)
    output_price:      Optional[float]       # costo per 1M token output (None = no stima)

    # ── Motori di difesa selezionati (globale, qualunque pipeline) ────
    # Difese alternative, non "il Blue più dei comparatori": una run può usarne
    # uno, alcuni o tutti. Il confronto fra i loro verdetti è post-processing su
    # run diverse, non più parte della run.
    defense_engines:  Optional[list[str]]  # selezione effettiva, ordine canonico
    run_blue:         Optional[bool]  # False → salta il Blue (assente/None = attivo)
    run_snyk:         Optional[bool]  # True → esegue snyk-agent-scan
    run_skillspector: Optional[bool]  # True → esegue NVIDIA SkillSpector
    run_cisco:        Optional[bool]  # True → esegue Cisco skill-scanner
    run_aig:          Optional[bool]  # True → esegue Tencent aig-skill-scan (LLM-only)
    run_skill_vetter: Optional[bool]  # True → esegue skill-vetter riprodotto via LLM (LLM-only)
    run_skills_sh:    Optional[bool]  # True → legge il verdetto già calcolato da skills.sh
    # True → forza lo scan solo-statico anche con credenziali LLM disponibili
    # (confronto con/senza LLM a parità di skill; vedi agents/skillspector_scanner.py
    # e agents/cisco_scanner.py). Ignorato se il motore non è già stato richiesto.
    skillspector_no_llm: Optional[bool]
    cisco_no_llm:        Optional[bool]
    # Interni, non riportati: node_blue lancia gli scan Snyk/skills.sh in
    # background (in parallelo al proprio scan, nessuno dei due dipende dai
    # risultati di Blue) e li passa a node_snyk/node_skills_sh via stato — vedi
    # graph/nodes.py:node_blue/node_snyk/node_skills_sh.
    _snyk_futures:       Optional[dict]
    _snyk_executor:      Optional[object]
    _skills_sh_futures:  Optional[dict]
    _skills_sh_executor: Optional[object]

    # ── Dati caricati (nodo load) ─────────────────────────────────────
    skill_contents: dict[str, str]   # {skill_name: testo SKILL.md}
    catalog:        dict             # catalogo già filtrato per K e tipologia

    # ── Pipeline blue-only ────────────────────────────────────────────
    external_skill_paths: list[str]  # path ai file SKILL.md forniti dall'utente

    # ── Pipeline blue-eval (skill-inject ground truth) ────────────────
    skill_inject_path:       Optional[str]        # root del repo skill-inject
    skill_inject_categories: Optional[list[str]]  # subset di {obvious, contextual}
    skill_inject_skills:     Optional[list[str]]  # filtro skill (None = tutte)
    # I record blue-eval riusano `injections` (InjectionRecord + campi eval), così
    # passano per gli stessi _compute_stats/_write_* di blue-only.
    blue_eval_stats:         Optional[dict]       # report_data del run blue-eval

    # ── Pipeline blue-eval-testing ────────────────────────────────────
    # Esegue il Tester SOLO sulle injection che il Blue NON ha flaggato come TP
    # (verdict != "TP"). I record TP (correttamente rilevati) vengono messi da
    # parte qui e ricomposti in `injections` prima del report, così la sezione
    # detection-accuracy resta sull'insieme COMPLETO mentre l'ASR è misurato solo
    # sul sottoinsieme mancato.
    blue_eval_testing_untested: list  # record TP non testati (ricomposti nel report)

    # ── Pipeline custom (5ª modalità — orchestrazione condizionale) ───
    # Config serializzata (PipelineConfig.to_dict) + riassunto degli step
    # eseguiti/saltati, scritto nel report per la riproducibilità.
    custom_config:  Optional[dict]
    custom_source:  Optional[dict]   # dettagli fonte risolti (folder/files/urls/entries)
    custom_steps:   Optional[dict]   # {source, blue, eval, tester, tester_mode, scope, skipped}

    # ── Output fase 1 — Red ───────────────────────────────────────────
    injections: list[InjectionRecord]
    # Lista che cresce nel tempo: Red la crea, Blue la arricchisce,
    # Tester+Judge completano le metriche.

    # ── Output finale — Report ────────────────────────────────────────
    report_data: Optional[dict]   # dati aggregati per JSON/MD/PDF

    # ── Errori ────────────────────────────────────────────────────────
    error: Optional[str]
