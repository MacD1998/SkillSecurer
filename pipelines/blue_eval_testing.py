"""
Pipeline: Blue Eval Testing
===========================
skill-inject ground truth → Blue → detection (TP/FP/FN) → Tester (sui soli
mancati) → report

Estende `blue-eval`: dopo aver misurato la detection del Blue contro le injection
note di skill-inject, esegue il Tester three-way (BASE→INJECTED→FIXED) SOLO sulle
injection che il Blue NON ha flaggato correttamente come TP (verdict != "TP",
cioè i FN mancati e i FP fuori bersaglio). Risponde alla domanda: "delle injection
che il Blue si è perso, quante in realtà eseguono davvero (ASR reale)?".

Riusa:
  • la detection + classificazione a due livelli di `blue-eval`
    (node_load_skill_inject, node_blue_eval, classify);
  • la macchina di esecuzione del Tester (graph.node_tester_judge), invariata —
    qui le serve solo una BASE pulita per-record (base_skill_path = SKILL.md
    sorgente) e l'eventuale FIXED dalle patch del Blue.

    graph:
      load_skill_inject → blue_eval → snyk → skillspector → cisco → aig → skills_sh → filter_non_tp
        ├─(ci sono mancati)→ tester_judge → merge_untested → report
        └─(nessun mancato)──────────────────────────────────→ report

snyk/skillspector sono no-op salvo i rispettivi flag (confronto Blue vs motori
terzi); girano sull'insieme COMPLETO (prima del filtro TP/non-TP), come la
detection-accuracy.

I record TP (rilevati correttamente) non vengono testati ma sono ricomposti in
`injections` prima del report: così la sezione detection-accuracy resta
sull'insieme COMPLETO, mentre ASR / three-way sono misurati sul solo sottoinsieme
mancato (i TP portano asr_pre=None → esclusi dai denominatori ASR, come i record
non testati di blue-only).

Stato richiesto (come blue-eval, più i parametri del tester):
  skill_inject_path, skill_inject_categories, skill_inject_skills (opz.),
  output_dir, parallel, max_attempts, docker_image,
  notes (opz.), input_price/output_price (opz.)
"""
from __future__ import annotations

from pathlib import Path

from langgraph.graph import StateGraph, END

import core.cli_output as cli
from graph import (
    SSE3State, node_snyk, node_skillspector, node_cisco, node_aig, node_skills_sh,
    node_tester_judge,
)

# Riuso diretto dei nodi/funzioni di blue-eval (nessuna duplicazione della
# detection): load + blue+classify + report sono identici.
from pipelines.blue_eval import (
    node_load_skill_inject,
    node_blue_eval,
    node_blue_eval_report,
)


# ── Nodo: filtra i non-TP e prepara il sottoinsieme per il Tester ─────

def node_filter_non_tp(state: SSE3State) -> dict:
    """
    Separa le injection classificate in:
      • non-TP (verdict != "TP")  → vanno al Tester (`injections`)
      • TP     (verdict == "TP")  → messe da parte (`blue_eval_testing_untested`),
                                     ricomposte nel report senza essere testate.

    Prepara ogni record non-TP per node_tester_judge:
      • base_skill_path = skill_path (SKILL.md sorgente pulito di skill-inject);
      • fix_path = patch del Blue applicate chirurgicamente all'iniettato, se ci
        sono (FP / patch parziali); i FN puri non hanno patch → FIXED saltato.
    """
    from agents.blue_agent import apply_patches_surgically

    records    = state.get("injections", []) or []
    output_dir = state["output_dir"]

    non_tp = [r for r in records if r.get("verdict") != "TP"]
    tp     = [r for r in records if r.get("verdict") == "TP"]

    # Nessun mancato: il Blue ha rilevato tutto → niente da testare. Si lascia
    # `injections` invariato (tutti TP) e si va dritti al report.
    if not non_tp:
        cli.phase("filter", "selecting Blue's misses for testing")
        cli.item(f"0/{len(records)} to test — Blue correctly flagged all as TP")
        cli.phase_done(timed=False)
        return {"injections": records, "blue_eval_testing_untested": []}

    fix_dir = output_dir / "fixed"
    n_fixed = 0
    for rec in non_tp:
        # BASE pulita = il SKILL.md sorgente da cui skill-inject ha iniettato.
        rec["base_skill_path"] = rec.get("skill_path") or rec.get("inj_path")
        # FIXED: applica le patch del Blue (se prodotte) all'iniettato. Per i FN
        # puri (nessuna patch) fix_path resta assente → il Tester valuta solo
        # BASE→INJECTED (FIXED None, gestito nativamente da node_tester_judge).
        patches = rec.get("patches_applied")
        if patches:
            try:
                injected = Path(rec["inj_path"]).read_text(encoding="utf-8", errors="ignore")
                fixed = apply_patches_surgically(injected, patches)
            except Exception:
                fixed = None
            if fixed is not None and fixed != injected:
                fp = fix_dir / Path(rec["inj_path"]).parent.name / "SKILL.md"
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(fixed, encoding="utf-8")
                rec["fix_path"] = str(fp)
                n_fixed += 1

    cli.phase("filter", "selecting Blue's misses for testing")
    cli.item(f"{len(non_tp)}/{len(records)} to test "
             f"(missed/misclassified) · {len(tp)} caught (skipped) · {n_fixed} with a Blue patch")
    cli.phase_done(timed=False)

    return {"injections": non_tp, "blue_eval_testing_untested": tp}


# ── Nodo: ricompone TP (non testati) + non-TP (testati) per il report ─

def node_merge_untested(state: SSE3State) -> dict:
    """Riunisce i record testati (non-TP, ora con metriche tester) con i TP messi
    da parte, così il report copre l'insieme COMPLETO. Riordina per leggibilità."""
    tested   = state.get("injections", []) or []
    untested = state.get("blue_eval_testing_untested", []) or []
    merged   = tested + untested
    merged.sort(key=lambda r: (r.get("category", ""), r.get("skill", ""),
                               r.get("injection_id", "")))
    return {"injections": merged}


# ── Graph ──────────────────────────────────────────────────────────────

def _route_after_load(state: SSE3State) -> str:
    return "end" if state.get("error") else "continue"


def _route_after_filter(state: SSE3State) -> str:
    """Tester solo se resta almeno una injection mancata da testare.

    Dopo il filtro `injections` contiene o il sottoinsieme non-TP (→ test) o, se
    il Blue ha rilevato tutto, l'insieme completo di soli TP (→ report diretto).
    Routing sul contenuto: c'è un record con verdict != "TP" da testare?
    """
    return ("test" if any(r.get("verdict") != "TP"
                          for r in state.get("injections", []))
            else "report")


def build() -> StateGraph:
    g = StateGraph(SSE3State)
    g.add_node("load_skill_inject", node_load_skill_inject)
    g.add_node("blue_eval",         node_blue_eval)
    g.add_node("snyk",              node_snyk)          # no-op se run_snyk non richiesto
    g.add_node("skillspector",      node_skillspector)  # no-op se run_skillspector non richiesto
    g.add_node("cisco",             node_cisco)          # no-op se run_cisco non richiesto
    g.add_node("aig",               node_aig)            # no-op se run_aig non richiesto
    g.add_node("skills_sh",         node_skills_sh)      # no-op se run_skills_sh non richiesto
    g.add_node("filter_non_tp",     node_filter_non_tp)
    g.add_node("tester_judge",      node_tester_judge)
    g.add_node("merge_untested",    node_merge_untested)
    g.add_node("report",            node_blue_eval_report)

    g.set_entry_point("load_skill_inject")
    g.add_conditional_edges("load_skill_inject", _route_after_load,
                            {"continue": "blue_eval", "end": END})
    g.add_edge("blue_eval",    "snyk")
    g.add_edge("snyk",         "skillspector")
    g.add_edge("skillspector", "cisco")
    g.add_edge("cisco",        "aig")
    g.add_edge("aig",          "skills_sh")
    g.add_edge("skills_sh",    "filter_non_tp")
    g.add_conditional_edges("filter_non_tp", _route_after_filter,
                            {"test": "tester_judge", "report": "report"})
    g.add_edge("tester_judge",   "merge_untested")
    g.add_edge("merge_untested", "report")
    g.add_edge("report", END)
    return g.compile()


def run(state: SSE3State) -> SSE3State:
    return build().invoke(state)
