"""
agents/__init__.py — re-export pubblico del package agents

Tutti gli agenti esportano qui i loro entry-point pubblici.
Questo è ciò che node_* in graph/nodes.py importa:

    from agents import blue_run, tester_run_queue, judge_evaluate
    from agents import generate
"""

# Red agent — generazione injection
from .red_agent     import generate, load_catalog

# Blue agent — scan + patch
from .blue_agent    import run as blue_run

# Tester agent — coda globale three-way (BASE/INJECTED/FIXED), affinity scheduling
from .tester_agent  import run_queue as tester_run_queue

# Judge agent — verdetto finale
from .judge_agent   import evaluate as judge_evaluate

# Docker runner — container target
from .docker_runner import (
    start_container,
    stop_container,
    run_target,
)

__all__ = [
    # Red
    "generate", "load_catalog",
    # Blue
    "blue_run",
    # Tester
    "tester_run_queue",
    # Judge
    "judge_evaluate",
    # Docker
    "start_container", "stop_container",
    "run_target",
]
