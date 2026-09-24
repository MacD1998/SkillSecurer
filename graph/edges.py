"""
Edges LangGraph — routing condizionale tra nodi
================================================
Le funzioni di edge ricevono lo stato e restituiscono
il nome del nodo successivo come stringa.

Usato con: g.add_conditional_edges(source, edge_fn, {label: target})
"""
from __future__ import annotations
from .state import SSE3State


def route_after_load(state: SSE3State) -> str:
    """Dopo il caricamento: controlla errori."""
    if state.get("error"):
        print(f"❌ {state['error']}")
        return "end"
    return "continue"


def route_after_red(state: SSE3State) -> str:
    """Dopo il Red: controlla che ci siano injection generate."""
    if state.get("error") or not state.get("injections"):
        print(f"❌ {state.get('error', 'Nessuna injection generata.')}")
        return "end"
    return "continue"
