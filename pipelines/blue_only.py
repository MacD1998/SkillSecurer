"""
Pipeline: Blue Only
===================
input_skills → Blue → Report

L'utente fornisce una lista di SKILL.md già esistenti da analizzare.
Non serve il Red agent — i file sono quelli da testare direttamente.

Caso d'uso: security audit di skill.md esistenti in produzione.

    graph:
      load_external → blue → report

Parametri aggiuntivi nello stato:
  external_skill_paths: list[str]   # path ai file da analizzare
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph import (
    SSE3State,
    node_load_external_skills, node_blue, node_snyk, node_skillspector, node_cisco, node_aig,
    node_skills_sh,
    node_report,
    route_after_load,
)


def build() -> StateGraph:
    g = StateGraph(SSE3State)

    g.add_node("load_external", node_load_external_skills)
    g.add_node("blue",          node_blue)
    g.add_node("snyk",          node_snyk)          # no-op se run_snyk non richiesto
    g.add_node("skillspector",  node_skillspector)  # no-op se run_skillspector non richiesto
    g.add_node("cisco",         node_cisco)          # no-op se run_cisco non richiesto
    g.add_node("aig",           node_aig)            # no-op se run_aig non richiesto
    g.add_node("skills_sh",     node_skills_sh)      # no-op se run_skills_sh non richiesto
    g.add_node("report",        node_report)

    g.set_entry_point("load_external")

    g.add_conditional_edges(
        "load_external",
        route_after_load,
        {"continue": "blue", "end": END},
    )
    g.add_edge("blue",         "snyk")
    g.add_edge("snyk",         "skillspector")
    g.add_edge("skillspector", "cisco")
    g.add_edge("cisco",        "aig")
    g.add_edge("aig",          "skills_sh")
    g.add_edge("skills_sh",    "report")
    g.add_edge("report", END)

    return g.compile()


def run(state: SSE3State) -> SSE3State:
    pipeline = build()
    return pipeline.invoke(state)
