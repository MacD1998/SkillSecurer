"""
Pipeline: Full Benchmark
========================
Red → Blue → Tester+Judge → Report

Flusso completo: genera injection, le rileva e fixa,
verifica l'eseguibilità PRE e POST patch, produce report.

    graph:
      load → red → blue → snyk → skillspector → cisco → aig → skills_sh → tester_judge → report

snyk/skillspector/cisco/aig/skills_sh sono no-op salvo --with-snyk/--with-skillspector/
--with-cisco/--with-aig/--with-skills-sh (confronto Blue vs motori terzi, vedi
graph.node_snyk / graph.node_skillspector / graph.node_cisco / graph.node_aig /
graph.node_skills_sh).
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph import (
    SSE3State,
    node_load, node_red, node_blue, node_snyk, node_skillspector, node_cisco, node_aig,
    node_skills_sh,
    node_tester_judge, node_report,
    route_after_load, route_after_red,
)


def build() -> StateGraph:
    g = StateGraph(SSE3State)

    # Nodi
    g.add_node("load",         node_load)
    g.add_node("red",          node_red)
    g.add_node("blue",         node_blue)
    g.add_node("snyk",         node_snyk)          # no-op se run_snyk non richiesto
    g.add_node("skillspector", node_skillspector)  # no-op se run_skillspector non richiesto
    g.add_node("cisco",        node_cisco)          # no-op se run_cisco non richiesto
    g.add_node("aig",          node_aig)            # no-op se run_aig non richiesto
    g.add_node("skills_sh",    node_skills_sh)      # no-op se run_skills_sh non richiesto
    g.add_node("tester_judge", node_tester_judge)
    g.add_node("report",       node_report)

    # Entry point
    g.set_entry_point("load")

    g.add_conditional_edges(
        "load",
        route_after_load,
        {"end": END, "continue": "red"},
    )
    g.add_conditional_edges(
        "red",
        route_after_red,
        {"continue": "blue", "end": END},
    )
    g.add_edge("blue",         "snyk")
    g.add_edge("snyk",         "skillspector")
    g.add_edge("skillspector", "cisco")
    g.add_edge("cisco",        "aig")
    g.add_edge("aig",          "skills_sh")
    g.add_edge("skills_sh",    "tester_judge")
    g.add_edge("tester_judge", "report")
    g.add_edge("report",       END)

    return g.compile()


def run(state: SSE3State) -> SSE3State:
    """Entry point della pipeline. Restituisce lo stato finale."""
    pipeline = build()
    return pipeline.invoke(state)
