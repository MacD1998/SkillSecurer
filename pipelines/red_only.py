"""
Pipeline: Red Only
==================
load → Red → Report

Genera solo le injection (nessun Blue, nessuna difesa, nessun tester): produce
le SKILL.md iniettate secondo il catalogo e il report che le descrive.

Caso d'uso: ispezionare/raccogliere le injection generate da RedInjector senza
spendere tempo/costo su un motore di difesa — es. per costruire un dataset, o
per validare a mano la qualità delle injection prima di lanciare una full.

    graph:
      load → red → report

Parametri di stato: stessi della pipeline full (skills_dir, skill_names,
catalog_path, parallel, max_files, difficulties, vuln_types), meno quelli che
servono solo a blue/tester (docker_image, max_attempts, engines).
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph import (
    SSE3State,
    node_load, node_red,
    node_report,
    route_after_load, route_after_red,
)


def build() -> StateGraph:
    g = StateGraph(SSE3State)

    g.add_node("load",   node_load)
    g.add_node("red",    node_red)
    g.add_node("report", node_report)

    g.set_entry_point("load")

    g.add_conditional_edges(
        "load",
        route_after_load,
        {"end": END, "continue": "red"},
    )
    g.add_conditional_edges(
        "red",
        route_after_red,
        {"continue": "report", "end": END},
    )
    g.add_edge("report", END)

    return g.compile()


def run(state: SSE3State) -> SSE3State:
    pipeline = build()
    return pipeline.invoke(state)
