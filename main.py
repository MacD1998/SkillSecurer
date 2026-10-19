"""
SSE3 — Skill Security Ecosystem v3
Entry point CLI — seleziona la pipeline da eseguire

Pipeline disponibili:
  full               Red→Blue→Tester→Judge→Report  (default)
  red-only           Red→Report (nessun Blue/difesa/tester)
  blue-only          input_skills→Blue→Report
  blue-eval          skill-inject→Blue→detection(TP/FP/FN)→Report
  blue-eval-testing  blue-eval + Tester sui soli mancati (verdict != TP)→Report
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

import core.cli_output as cli
from pipelines.custom_config import DEFENSE_ENGINES, clean_engines

load_dotenv(Path(__file__).parent / ".env")


# ── Motori di difesa ──────────────────────────────────────────────────
# I vecchi --with-X sono alias additivi di --defense: erano add-on del Blue,
# quindi "solo --with-cisco" ha sempre significato "blue + cisco" e continua a
# significarlo. Solo un --defense esplicito può togliere il Blue dalla difesa.

_WITH_ALIASES = (("with_skillspector", "skillspector"), ("with_cisco", "cisco"),
                 ("with_aig", "aig"), ("with_skill_vetter", "skill_vetter"),
                 ("with_snyk", "snyk"), ("with_skills_sh", "skills_sh"))


def _defense_from_args(args: argparse.Namespace, *, implicit_blue: bool) -> list[str]:
    """Motori richiesti dalla riga di comando.

    implicit_blue=True (pipeline fisse): senza --defense la difesa è il Blue,
    più gli eventuali alias --with-X. implicit_blue=False (pipeline custom): solo
    ciò che è stato chiesto ESPLICITAMENTE, perché lì i flag CLI si sommano ai
    motori del preset e un default implicito riaccenderebbe il Blue su un preset
    che lo aveva spento.
    """
    base = list(args.defense) if args.defense else (["blue"] if implicit_blue else [])
    return clean_engines(base + [eng for attr, eng in _WITH_ALIASES if getattr(args, attr)])


def _engine_state(engines: list[str]) -> dict:
    """Flag di stato letti dai nodi (uno per motore) + la selezione completa."""
    return {"defense_engines": engines,
            "run_blue":         "blue"         in engines,
            "run_skillspector": "skillspector" in engines,
            "run_cisco":        "cisco"        in engines,
            "run_aig":          "aig"          in engines,
            "run_skill_vetter": "skill_vetter" in engines,
            "run_snyk":         "snyk"         in engines,
            "run_skills_sh":    "skills_sh"    in engines}


def _no_llm_state(args: argparse.Namespace) -> dict:
    """Flag di stato per forzare skillspector/cisco a solo-statico anche con
    credenziali LLM disponibili (confronto con/senza LLM a parità di skill —
    vedi agents/skillspector_scanner.py, agents/cisco_scanner.py). No-op se il
    motore non è tra quelli selezionati."""
    return {"skillspector_no_llm": bool(args.skillspector_no_llm),
            "cisco_no_llm":        bool(args.cisco_no_llm)}


def _check_api_key() -> None:
    """Verifica che almeno una API key sia disponibile."""
    keys = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"]
    available = [k for k in keys if os.environ.get(k)]
    if not available:
        cli.error("No API key found. Set one of these env vars in .env: "
                  + ", ".join(keys))
        sys.exit(1)
    # Provider in uso → solo in debug
    explicit = os.environ.get("LLM_PROVIDER", "").strip()
    if explicit:
        cli.debug(f"  🔑 Explicit provider: {explicit}")
    else:
        provider = {
            "DEEPSEEK_API_KEY":  "deepseek",
            "OPENROUTER_API_KEY":"openrouter",
            "OPENAI_API_KEY":    "openai",
        }[available[0]]
        cli.debug(f"  🔑 Provider auto-detect: {provider} (via {available[0]})")


def _check_docker(docker_image: str) -> None:
    """Blocca subito se il tester non potrebbe girare.

    Chiamata SOLO dalle pipeline che eseguono il tester. Senza questo controllo
    il primo contatto con Docker avviene a metà run (node_tester_judge), dopo che
    Red e Blue hanno già speso in chiamate LLM: su un run grande sono diversi
    dollari buttati per fermarsi su un demone spento o un'immagine mai costruita.
    """
    from agents.docker_runner import preflight

    problems = preflight(docker_image)
    if not problems:
        return
    cli.error("The tester requires Docker, but the environment isn't ready:")
    for p in problems:
        cli.error(f"  • {p}")
    cli.error("No LLM calls were made: fix this and re-run.")
    sys.exit(1)


def _print_header(args: argparse.Namespace, pipeline: str) -> None:
    # Header dettagliato → debug; l'header pulito del run è emesso da node_load.
    cli.debug(f"  SSE3 — Pipeline: {pipeline.upper()}")
    if pipeline == "full":
        cli.debug(f"  Skills: {args.skills}  Difficulties: {args.difficulties}  Vuln types: {args.vuln_types}")
        cli.debug(f"  Attempts: {args.max_attempts}  Parallel: {getattr(args,'parallel',4)}")
    elif pipeline == "red-only":
        cli.debug(f"  Skills: {args.skills}  Difficulties: {args.difficulties}  Vuln types: {args.vuln_types}")
        cli.debug(f"  Parallel: {getattr(args,'parallel',4)}")
    elif pipeline == "blue-only":
        cli.debug(f"  Input skills: {args.input_skills}")
    cli.debug(f"  Output: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="SSE3 — Skill Security Ecosystem v3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── Pipeline ─────────────────────────────────────────────────────
    parser.add_argument(
        "--pipeline",
        choices=["full", "red-only", "blue-only", "blue-eval", "blue-eval-testing", "custom"],
        default="full",
        help="Pipeline to run (default: full)"
    )

    # ── Output (comune a tutte le pipeline) ──────────────────────────
    parser.add_argument(
        "--output", required=True,
        help="Output folder for results"
    )
    parser.add_argument(
        "--notes", default=None,
        help="Free-text note about the test, saved into the report (results.json + MD/PDF/HTML)"
    )
    parser.add_argument(
        "--input-price", type=float, default=None,
        help="Cost per 1M input tokens (USD) — enables the cost estimate in the report"
    )
    parser.add_argument(
        "--output-price", type=float, default=None,
        help="Cost per 1M output tokens (USD) — enables the cost estimate in the report"
    )
    parser.add_argument(
        "--defense", nargs="+", default=None, metavar="ENGINE",
        choices=list(DEFENSE_ENGINES),
        help="Defense engines to run on each skill: "
             + " ".join(DEFENSE_ENGINES) + ". These are ALTERNATIVE defenses, not a "
             "comparison: run one pass with only 'blue', another with only "
             "'cisco', then compare the two reports afterwards. "
             "Default (flag absent): 'blue'. eval and tester require 'blue' among the "
             "engines — the full/blue-eval/blue-eval-testing pipelines enforce it."
    )
    parser.add_argument(
        "--with-snyk", action="store_true",
        help="Additive alias for --defense snyk (compatibility)."
    )
    parser.add_argument(
        "--with-skillspector", action="store_true",
        help="Additive alias for --defense skillspector (compatibility)."
    )
    parser.add_argument(
        "--with-cisco", action="store_true",
        help="Additive alias for --defense cisco (compatibility)."
    )
    parser.add_argument(
        "--with-aig", action="store_true",
        help="Additive alias for --defense aig (compatibility). Tencent aig-skill-scan "
             "(SkillTrustBench T01-T09) — LLM-only engine, no --no-llm variant."
    )
    parser.add_argument(
        "--with-skill-vetter", action="store_true",
        help="Additive alias for --defense skill_vetter (compatibility). \"skill-vetter\" "
             "(OpenClaw skill, MIT-0) reproduced via LLM — LLM-only engine, no "
             "--no-llm variant (see agents/skill_vetter_scanner.py)."
    )
    parser.add_argument(
        "--with-skills-sh", action="store_true",
        help="Additive alias for --defense skills_sh (compatibility). No live scan: "
             "reads the verdict already computed by skills.sh (3 engines: "
             "agentTrustHub, socket, snyk — meta.json in skills_sh_dataset next to "
             "the file), no-op for skills outside the dataset."
    )
    parser.add_argument(
        "--skillspector-no-llm", action="store_true",
        help="Force SkillSpector to static-only scan (regex/AST/YARA/OSV.dev) even "
             "with LLM credentials available — to compare results with/without "
             "LLM on the same skill. No-op if skillspector isn't among the requested engines."
    )
    parser.add_argument(
        "--cisco-no-llm", action="store_true",
        help="Force Cisco skill-scanner to static-only scan even with LLM credentials "
             "available — to compare results with/without LLM on the same "
             "skill. No-op if cisco isn't among the requested engines."
    )

    # ── Parametri pipeline full ───────────────────────────────────────
    full = parser.add_argument_group("Pipeline: full")
    full.add_argument(
        "--skills", nargs="+", default=None,
        help="Names of the skills to test (e.g. git calendar)"
    )
    full.add_argument(
        "--max-files", type=int, default=None,
        help="Cap the number of generated injections (safety net)"
    )
    full.add_argument(
        "--parallel", type=int, default=20,
        help="Parallel workers for red/blue + containers in the tester pool"
    )
    full.add_argument(
        "--max-attempts", type=int, default=5,
        help="Number of legitimate prompts generated and replayed on "
             "BASE/INJECTED/FIXED per injection"
    )
    full.add_argument(
        "--difficulties", nargs="+", default=None, metavar="K",
        help="Filter by difficulty: K1 K2 K3"
    )
    full.add_argument(
        "--vuln-types", nargs="+", default=None, metavar="TYPE",
        help="Filter by type: data_exfiltration supply_chain ..."
    )
    full.add_argument(
        "--skills-dir", default=None,
        help="Base skills directory (default: skill-inject/data/skills)"
    )

    # ── Parametri pipeline blue-only ──────────────────────────────────
    blue = parser.add_argument_group("Pipeline: blue-only")
    blue.add_argument(
        "--input-skills", nargs="+", default=None, metavar="PATH",
        help="Path to SKILL.md files or folders to audit. "
             "Folders are scanned recursively. "
             "Example: --input-skills file1.md SKILLS/ shared/skills/"
    )

    # ── Parametri pipeline blue-eval ──────────────────────────────────
    beval = parser.add_argument_group("Pipeline: blue-eval")
    beval.add_argument(
        "--skill-inject-categories", choices=["obvious", "contextual", "both"],
        default="both",
        help="skill-inject injection categories to evaluate (default: both)"
    )
    beval.add_argument(
        "--skill-inject-skills", nargs="+", default=None, metavar="SKILL",
        help="Filter by skill type (e.g. docx pptx calendar). Default: all."
    )
    beval.add_argument(
        "--skill-inject-path", default="skill-inject",
        help="Path to the skill-inject repo (default: skill-inject/ relative to the project root)"
    )

    # ── Parametri pipeline custom ─────────────────────────────────────
    custom = parser.add_argument_group("Pipeline: custom")
    custom.add_argument(
        "--config", default=None,
        help="Path to a PipelineConfig JSON file (custom pipeline)"
    )
    custom.add_argument(
        "--preset", default=None,
        help="Name of a custom preset saved in pipelines/custom/ (custom pipeline)"
    )

    # ── Docker (comune) ───────────────────────────────────────────────
    parser.add_argument("--docker-image", default="sse3-target")

    args   = parser.parse_args()
    base   = Path(__file__).parent
    outdir = base / args.output

    _check_api_key()
    _print_header(args, args.pipeline)

    # Live token/cost: sotto WebUI (SSE_EMIT_TOKENS) registra un emitter che
    # pubblica snapshot parziali throttled su stdout → il WebUI li mostra live.
    # Un heartbeat forza un emit ogni 3s anche senza nuove chiamate LLM, così il
    # pannello non resta fermo durante fasi mute (scan skillspector/cisco/aig,
    # target agent in Docker — vedi token_tracker.set_emitter).
    if os.environ.get("SSE_EMIT_TOKENS"):
        try:
            import core.token_tracker as token_tracker
            _ip, _op = args.input_price, args.output_price
            token_tracker.set_emitter(
                lambda snap: cli.emit_token_usage(snap, _ip, _op))
        except Exception as e:
            # Non blocca il run (il pannello live è un accessorio), ma il
            # silenzio faceva sembrare rotta la WebUI senza alcun indizio.
            cli.warn(f"Live token tracking disabled: {e} — the WebUI token/cost "
                     f"panel will stay empty (the final report is still complete)")

    # Le pipeline fisse diverse da blue-only eseguono eval e/o tester, che si
    # reggono sui finding e sulla patch del Blue: una difesa senza 'blue' le
    # renderebbe vuote. Stesso gate applicato dal validatore della custom.
    engines = _defense_from_args(args, implicit_blue=args.pipeline != "custom")
    if args.pipeline in ("full", "blue-eval", "blue-eval-testing") and "blue" not in engines:
        parser.error(f"--defense: the {args.pipeline} pipeline requires the 'blue' engine "
                     f"(it runs eval and/or tester, which evaluate its findings and its patch). "
                     f"To run only third-party engines use --pipeline blue-only.")

    # Proxy locale per token/costo REALI di skillspector/cisco/aig (girano come
    # subprocesso esterno, altrimenti invisibili a token_tracker — vedi
    # agents/llm_proxy.py). Avviato sempre (costo nullo se il motore non è
    # richiesto): la pipeline custom decide gli engine effettivi solo dopo il
    # merge col preset, troppo tardi per condizionare l'avvio qui. Se fallisce,
    # gli scanner ricadono su openrouter.ai diretto (solo tracking perso).
    from agents import llm_proxy
    llm_proxy.start()

    # ── Pipeline: full ────────────────────────────────────────────────
    if args.pipeline == "full":
        if not args.skills:
            parser.error("--skills is required for the full pipeline")
        _check_docker(args.docker_image)   # la full esegue sempre il tester

        from graph import SSE3State
        from pipelines import full_benchmark

        skills_dir = (Path(args.skills_dir) if args.skills_dir
                      else base / "skill-inject" / "data" / "skills")

        state = SSE3State(
            skills_dir=        skills_dir,
            skill_names=       args.skills,
            output_dir=        outdir,
            catalog_path=      base / "config" / "catalog.json",
            parallel=          args.parallel,
            max_files=         args.max_files,
            max_attempts=      args.max_attempts,
            docker_image=      args.docker_image,
            difficulties=      args.difficulties,
            vuln_types=        args.vuln_types,
            notes=             args.notes,
            input_price=       args.input_price,
            output_price=      args.output_price,
            **_engine_state(engines),
            **_no_llm_state(args),
        )
        full_benchmark.run(state)

    # ── Pipeline: red-only ──────────────────────────────────────────────
    elif args.pipeline == "red-only":
        if not args.skills:
            parser.error("--skills is required for the red-only pipeline")

        from graph import SSE3State
        from pipelines import red_only

        skills_dir = (Path(args.skills_dir) if args.skills_dir
                      else base / "skill-inject" / "data" / "skills")

        state = SSE3State(
            skills_dir=        skills_dir,
            skill_names=       args.skills,
            output_dir=        outdir,
            catalog_path=      base / "config" / "catalog.json",
            parallel=          args.parallel,
            max_files=         args.max_files,
            difficulties=      args.difficulties,
            vuln_types=        args.vuln_types,
            notes=             args.notes,
            input_price=       args.input_price,
            output_price=      args.output_price,
            # Nessun motore di difesa gira: esplicito (non assente) così il
            # report non ricade sul default retrocompatibile "blue sempre
            # girato" e mostra "—" invece di un fuorviante 0% di detection.
            **_engine_state([]),
        )
        red_only.run(state)

    # ── Pipeline: blue-only ───────────────────────────────────────────
    elif args.pipeline == "blue-only":
        if not args.input_skills:
            parser.error("--input-skills is required for the blue-only pipeline")

        from graph import SSE3State
        from pipelines import blue_only

        state = SSE3State(
            output_dir=           outdir,
            external_skill_paths= args.input_skills,
            docker_image=         args.docker_image,
            parallel=             getattr(args, "parallel", 4),
            max_files=            args.max_files,
            notes=                args.notes,
            input_price=          args.input_price,
            output_price=         args.output_price,
            **_engine_state(engines),
            **_no_llm_state(args),
        )
        blue_only.run(state)

    # ── Pipeline: blue-eval ───────────────────────────────────────────
    elif args.pipeline == "blue-eval":
        from graph import SSE3State
        from pipelines import blue_eval

        cats = (["obvious", "contextual"] if args.skill_inject_categories == "both"
                else [args.skill_inject_categories])
        si_path = Path(args.skill_inject_path)
        if not si_path.is_absolute():
            si_path = base / si_path

        state = SSE3State(
            output_dir=              outdir,
            skill_inject_path=       str(si_path),
            skill_inject_categories= cats,
            skill_inject_skills=     args.skill_inject_skills,
            max_files=               args.max_files,
            parallel=                getattr(args, "parallel", 5),
            notes=                   args.notes,
            input_price=             args.input_price,
            output_price=            args.output_price,
            **_engine_state(engines),
            **_no_llm_state(args),
        )
        blue_eval.run(state)

    # ── Pipeline: blue-eval-testing ───────────────────────────────────
    # Come blue-eval, ma esegue il Tester three-way SOLO sulle injection che il
    # Blue NON ha flaggato come TP (i mancati). Riusa i parametri del tester
    # (--max-attempts, --docker-image) oltre a quelli di blue-eval.
    elif args.pipeline == "blue-eval-testing":
        _check_docker(args.docker_image)   # esegue il tester sui mancati del Blue

        from graph import SSE3State
        from pipelines import blue_eval_testing

        cats = (["obvious", "contextual"] if args.skill_inject_categories == "both"
                else [args.skill_inject_categories])
        si_path = Path(args.skill_inject_path)
        if not si_path.is_absolute():
            si_path = base / si_path

        state = SSE3State(
            output_dir=              outdir,
            skill_inject_path=       str(si_path),
            skill_inject_categories= cats,
            skill_inject_skills=     args.skill_inject_skills,
            max_files=               args.max_files,
            max_attempts=            args.max_attempts,
            docker_image=            args.docker_image,
            parallel=                getattr(args, "parallel", 5),
            notes=                   args.notes,
            input_price=             args.input_price,
            output_price=            args.output_price,
            **_engine_state(engines),
            **_no_llm_state(args),
        )
        blue_eval_testing.run(state)

    # ── Pipeline: custom ──────────────────────────────────────────────
    # Combinazione configurabile a runtime dei 4 step (fonte/blue/eval/tester).
    # Config da file JSON (--config) o da preset salvato per nome (--preset).
    # La matrice di validità è applicata da validate_or_raise (gate duro backend).
    elif args.pipeline == "custom":
        import json as _json
        from graph import SSE3State
        from pipelines import custom as custom_pipe
        from pipelines.custom_config import PipelineConfig, validate_or_raise

        if bool(args.config) == bool(args.preset):
            parser.error("custom: specify exactly one of --config and --preset")

        if args.config:
            cfg_path = Path(args.config)
            if not cfg_path.is_absolute():
                cfg_path = base / cfg_path
            if not cfg_path.exists():
                cli.error(f"Config not found: {cfg_path}")
                sys.exit(1)
            cfg = PipelineConfig.from_dict(_json.loads(cfg_path.read_text(encoding="utf-8")))
        else:
            from pipelines.custom_store import load_custom_pipeline
            try:
                cfg = load_custom_pipeline(args.preset)
            except FileNotFoundError as e:
                cli.error(str(e))
                sys.exit(1)

        try:
            validate_or_raise(cfg)
        except ValueError as e:
            cli.error(str(e))
            sys.exit(1)

        # Solo se questa configurazione prevede davvero il tester: una custom
        # con solo Blue non ha bisogno di Docker e non va bloccata.
        if cfg.tester.enabled:
            _check_docker(args.docker_image)

        state = SSE3State(
            output_dir=    outdir,
            custom_config= cfg.to_dict(),
            max_files=     args.max_files,
            max_attempts=  args.max_attempts,
            docker_image=  args.docker_image,
            parallel=      getattr(args, "parallel", 5),
            notes=         args.notes,
            input_price=   args.input_price,
            output_price=  args.output_price,
            # I motori CLI sono ADDITIVI rispetto al preset (pipelines/custom.py
            # li unisce a cfg.defense.engines): un preset salvato dalla WebUI si
            # porta dietro i propri, e --defense/--with-X ne abilitano altri senza
            # doverlo riscrivere. Qui NON c'è il default implicito 'blue' delle
            # pipeline fisse, altrimenti un preset con la difesa spenta se lo
            # ritroverebbe acceso.
            **_engine_state(engines),
            **_no_llm_state(args),
        )
        custom_pipe.run(state)

    llm_proxy.stop()


if __name__ == "__main__":
    main()
