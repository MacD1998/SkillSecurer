"""
webui/app.py — Local WebUI for the SSE benchmark
=============================================
Self-contained Flask server that runs ALONGSIDE the existing CLI pipeline.
It does NOT import or touch main.py / agents / graph: it spawns `main.py` as a
subprocess and streams its output to the browser over Server-Sent Events.

Why a PTY (and not a plain pipe)?
  cli_output.py gates the tester progress bar behind `sys.stdout.isatty()`.
  Under a normal captured pipe that check is False and the bar never prints.
  Running main.py under a pseudo-terminal makes isatty() True, so the live
  bar (and its `att N/M · VERSION` label) streams to us verbatim — without
  modifying a single line of existing code.

Stack: Flask (threaded) + stdlib only. SSE via a /stream text/event-stream
endpoint. Launches http://localhost:5050 in the browser automatically.
"""
import datetime as dt
import json
import os
import pty
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

from flask import Flask, Response, request, jsonify, send_file, abort

BASE = Path(__file__).resolve().parent.parent  # project root (this file lives in webui/)
PORT = 5050

# Questo file vive in webui/, quindi sys.path[0] di default è webui/ e non la
# project root: senza questa riga tutti gli import lazy verso i pacchetti di
# progetto (core, agents, graph, pipelines, postprocess, reporting) falliscono
# con ModuleNotFoundError alla prima richiesta che li tocca.
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

# Carica .env così OPENROUTER_API_KEY è disponibile per /api/models (la pipeline
# vera la ricarica comunque in main.py; qui serve solo per il fetch dei modelli).
try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env")
except Exception:
    pass

app = Flask(__name__, static_folder=None)


# Ordina per popolarità (rank di skills_sh_dataset, via meta.json accanto al
# SKILL.md) quando disponibile — stessa logica di graph.nodes._popularity_rank,
# duplicata qui perché webui.py resta volutamente indipendente da graph/agents
# (spawna sempre main.py come subprocess, non importa moduli della pipeline).
# name_lower come fallback/tiebreak tiene l'ordine alfabetico per tutto ciò che
# non fa parte del dataset (nessun meta.json accanto).
def _popularity_key(meta_dir: Path, name: str) -> tuple:
    meta_path = meta_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            rank = meta.get("rank")
            if isinstance(rank, (int, float)):
                return (0, rank, name.lower())
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    return (1, 0, name.lower())

# Bar redraw line, e.g. "  [████░░░░] 12/120  data_exfiltration/K3 · att 3/5 · INJECTED"
_BAR_RE = re.compile(r"\[[█░ ]*\]\s*(\d+)\s*/\s*(\d+)\s*(.*)$")
# Each PTY token terminated by \r (progress redraw / clear) or \n (normal print).
_TERM_RE = re.compile(r"[^\r\n]*[\r\n]")
# A path ending in report.html, captured from the footer "report  <path>" line.
_REPORT_RE = re.compile(r"(\S+report\.html)\b")


# ── Run manager ────────────────────────────────────────────────────────
class Run:
    """Holds the single active benchmark run and fans events out to SSE clients."""

    def __init__(self):
        self.lock = threading.Lock()
        self.proc = None
        self.master_fd = None
        self.running = False
        self.subscribers: list[queue.Queue] = []
        self.history: list[dict] = []      # replayed to late-joining streams
        self.last_progress: dict | None = None
        self.last_tokens: dict | None = None   # latest live token/cost snapshot
        self.report_path: str | None = None
        self.params: dict = {}

    # -- pub/sub -------------------------------------------------------
    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self.lock:
            backlog = list(self.history)
            last = self.last_progress
            last_tok = self.last_tokens
            self.subscribers.append(q)
        for ev in backlog:
            q.put(ev)
        if last_tok:
            q.put(last_tok)
        if last:
            q.put(last)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self.lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def emit(self, ev: dict) -> None:
        """Structural event: kept in history (so reloads replay it) and fanned out."""
        with self.lock:
            self.history.append(ev)
            subs = list(self.subscribers)
        for q in subs:
            q.put(ev)

    def emit_progress(self, done: int, total: int, label: str) -> None:
        """Transient bar update: NOT stored in history (only the latest is kept)."""
        ev = {"t": "progress", "done": done, "total": total, "label": label}
        with self.lock:
            self.last_progress = ev
            subs = list(self.subscribers)
        for q in subs:
            q.put(ev)

    def emit_tokens(self, usage: dict) -> None:
        """Live token/cost snapshot: only the latest is kept (replayed to new subs)."""
        ev = {"t": "tokens", **usage}
        with self.lock:
            self.last_tokens = ev
            subs = list(self.subscribers)
        for q in subs:
            q.put(ev)

    def reset(self, params: dict) -> None:
        with self.lock:
            self.history = []
            self.last_progress = None
            self.last_tokens = None
            self.report_path = None
            self.params = params
            self.running = True


RUN = Run()


# ── PTY reader ─────────────────────────────────────────────────────────
def _split_tokens(s: str):
    """Split a chunk into completed line-tokens (\\r or \\n terminated) + remainder."""
    toks, last = [], 0
    for m in _TERM_RE.finditer(s):
        toks.append(m.group()[:-1])   # drop the terminator char
        last = m.end()
    return toks, s[last:]


_TOKENS_MARKER = "@@SSE_TOKENS@@"


def _classify(run: Run, tok: str) -> None:
    line = tok.rstrip()
    if not line.strip():
        return
    # Live token/cost snapshot (machine-readable) → tokens event, NOT human log.
    idx = line.find(_TOKENS_MARKER)
    if idx != -1:
        try:
            usage = json.loads(line[idx + len(_TOKENS_MARKER):])
            run.emit_tokens(usage)
        except Exception:
            pass
        return
    m = _BAR_RE.search(line)
    if m:
        run.emit_progress(int(m.group(1)), int(m.group(2)), m.group(3).strip())
        return
    if "report" in line.lower():
        rm = _REPORT_RE.search(line)
        if rm:
            run.report_path = rm.group(1)
    run.emit({"t": "line", "l": line})


def _reader(run: Run, master_fd: int, proc: subprocess.Popen) -> None:
    pending = ""
    try:
        while True:
            try:
                data = os.read(master_fd, 4096)
            except OSError:
                break
            if not data:
                break
            pending += data.decode("utf-8", "replace")
            toks, pending = _split_tokens(pending)
            for tok in toks:
                _classify(run, tok)
    finally:
        if pending.strip():
            _classify(run, pending)
        code = proc.wait()
        try:
            os.close(master_fd)
        except OSError:
            pass
        with run.lock:
            run.running = False
        run.emit({"t": "end", "code": code, "report": run.report_path})


# ── Build the main.py command line ─────────────────────────────────────
def build_argv(p: dict) -> list[str]:
    """La webui lancia SEMPRE la pipeline custom (main.py --pipeline custom
    --config <tmp.json>) — le 4 pipeline "predefinite" sono solo template che
    pre-valorizzano lo stesso wizard lato client (webui/index.html), uniformi
    coi preset salvati/nuovi. Le pipeline dedicate (full/blue-only/blue-eval/
    blue-eval-testing) restano disponibili per uso CLI diretto (main.py),
    semplicemente non più raggiunte da qui."""
    py = sys.executable or "python3"
    out = (p.get("output") or "results/webui_run").strip()
    argv = [py, "main.py", "--pipeline", "custom", "--output", out]

    notes = (p.get("notes") or "").strip()
    if notes:
        argv += ["--notes", notes]

    # Prezzi token (USD per 1M) → abilitano la stima di costo nel report.
    # Pre-compilati dalla UI quando si seleziona un modello con prezzi.
    ip = p.get("input_price")
    op = p.get("output_price")
    if ip not in (None, ""):
        argv += ["--input-price", str(ip)]
    if op not in (None, ""):
        argv += ["--output-price", str(op)]

    # La config (source/defense/eval/tester, con i motori di difesa selezionati
    # in defense.engines) arriva dalla UI come dict (PipelineConfig.to_dict). La
    # serializziamo in un JSON co-locato con l'output e passiamo --config: le
    # run non salvate NON inquinano la dir dei preset (quelli salvati girano
    # via --preset).
    cfg = p.get("custom_config") or {}
    cfg_dir = BASE / out
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "_custom_config.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    argv += ["--config", str(cfg_path)]
    argv += ["--max-attempts", str(int(p.get("max_attempts") or 5))]
    argv += ["--parallel", str(int(p.get("parallel") or 20))]
    mf = p.get("max_files")
    if mf not in (None, "", 0, "0"):
        argv += ["--max-files", str(int(mf))]
    return argv


def start_run(params: dict) -> list[str]:
    argv = build_argv(params)
    master_fd, slave_fd = pty.openpty()

    env = dict(os.environ)
    env["COLUMNS"] = "120"          # stable widths for boxes / progress bar
    env["LINES"] = "50"
    env["TERM"] = "xterm-256color"  # make isatty() path emit the live bar
    env["PYTHONUNBUFFERED"] = "1"
    env.pop("SSE_VERBOSE", None)     # keep the clean structured output
    env["SSE_EMIT_TOKENS"] = "1"     # emit live token/cost snapshots on stdout

    # Modello selezionato nella UI → SECURITY_MODEL per il subprocess. Se nessun
    # modello è selezionato si lascia il default del .env (env ereditato così com'è).
    model = (params.get("model") or "").strip()
    if model:
        env["SECURITY_MODEL"] = model

    # Override per-agente (pannello "Model per agent" della UI, opzionale): solo
    # gli agenti rilevanti per la pipeline selezionata sono mostrati lì, e solo i
    # ruoli valorizzati arrivano qui. Ognuno ricade su SECURITY_MODEL (sopra) se
    # non impostato — vedi llm_factory.build_llm.
    agent_env = {
        "red":          "RED_MODEL",
        "blue_scan":    "BLUE_SCAN_MODEL",
        "blue_patch":   "BLUE_PATCH_MODEL",
        "target":       "TARGET_MODEL",
        "env":          "ENV_MODEL",
        "judge":        "JUDGE_MODEL",
        "tester_judge": "TESTER_MODEL",
        "validator":    "VALIDATOR_MODEL",
    }
    for role, val in (params.get("agent_models") or {}).items():
        env_var = agent_env.get(role)
        if env_var and isinstance(val, str) and val.strip():
            env[env_var] = val.strip()

    # Provider da escludere dal routing OpenRouter (selezionati nella UI). Comma-
    # separated → OPENROUTER_PROVIDER_IGNORE; con sort=price attivo il routing
    # sceglie il più economico TRA i rimanenti (vedi llm_factory).
    prov_ignore = (params.get("provider_ignore") or "").strip()
    if prov_ignore:
        env["OPENROUTER_PROVIDER_IGNORE"] = prov_ignore

    # Override dei system prompt degli agenti (dalla UI). Solo i valori non vuoti;
    # scritti in un JSON co-locato con l'output, path passato via env al subprocess.
    overrides = {k: v for k, v in (params.get("system_prompts") or {}).items()
                 if isinstance(v, str) and v.strip()}
    if overrides:
        out = (params.get("output") or "results/webui_run").strip()
        pdir = BASE / out
        pdir.mkdir(parents=True, exist_ok=True)
        ppath = pdir / "_prompt_overrides.json"
        ppath.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8")
        env["SSE3_PROMPT_OVERRIDES"] = str(ppath)

    proc = subprocess.Popen(
        argv, cwd=str(BASE),
        stdout=slave_fd, stderr=slave_fd, stdin=slave_fd,
        close_fds=True, env=env,
    )
    os.close(slave_fd)

    RUN.reset(params)
    RUN.proc = proc
    RUN.master_fd = master_fd
    threading.Thread(target=_reader, args=(RUN, master_fd, proc), daemon=True).start()
    return argv


# ── Routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(str(BASE / "webui" / "index.html"))


@app.route("/prompts")
def prompts():
    """System prompt DI DEFAULT per ogni agente → prefill dei textarea nella UI."""
    try:
        from agents.prompt_registry import default_prompts
        return jsonify({"ok": True, "prompts": default_prompts()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "prompts": []}), 500


@app.route("/run", methods=["POST"])
def run():
    if RUN.running:
        return jsonify({"ok": False, "error": "A run is already in progress."}), 409
    params = request.get_json(force=True, silent=True) or {}
    try:
        argv = start_run(params)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "argv": argv})


@app.route("/stop", methods=["POST"])
def stop():
    if RUN.running and RUN.proc:
        try:
            RUN.proc.terminate()
        except Exception:
            pass
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    q = RUN.subscribe()

    def gen():
        yield _sse({"t": "status", "running": RUN.running})
        if not RUN.running:
            # No run in flight: nothing to stream. Close now instead of idling
            # on keepalives forever — the client reopens /stream when it starts
            # a run (or reconnects to one already in flight, handled above).
            RUN.unsubscribe(q)
            return
        try:
            while True:
                try:
                    ev = q.get(timeout=15)
                except queue.Empty:
                    yield ": keepalive\n\n"     # comment line keeps the socket warm
                    continue
                yield _sse(ev)
                if ev.get("t") == "end":
                    break
        finally:
            RUN.unsubscribe(q)

    return Response(gen(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })


@app.route("/report")
def report():
    rp = RUN.report_path
    path = Path(rp) if rp else (BASE / (RUN.params.get("output") or "results/webui_run") / "report.html")
    if not path.is_absolute():
        path = BASE / path
    if not path.exists():
        abort(404, "report.html not generated yet")
    return send_file(str(path))


# ── Filesystem pickers (form autocomplete + directory browser) ─────────
_SKILLS_DIR = BASE / "skill-inject" / "data" / "skills"
# Browsing root: filesystem root so any WSL folder (/home, /mnt/c, …) is reachable
# from the directory browser. Local single-user tool on localhost → no confinement
# beyond the FS root. Override with SSE_BROWSE_ROOT to restrict (e.g. to $HOME).
_BROWSE_LIMIT = Path(os.environ.get("SSE_BROWSE_ROOT", "/")).resolve()


@app.route("/api/skills")
def api_skills():
    """Subdirectory names under skill-inject/data/skills (one dir = one skill)."""
    if not _SKILLS_DIR.is_dir():
        return jsonify([])
    names = sorted(p.name for p in _SKILLS_DIR.iterdir() if p.is_dir())
    return jsonify(names)


@app.route("/api/skill-inject-base")
def api_skill_inject_base():
    """Skill BASE pulite di skill-inject (data/skills/<skill>/SKILL.md) come fonte
    per il Red della pipeline custom. Ritorna {path, files:[relativi]} con SOLO i
    SKILL.md (non i .md di supporto examples/references), stesso formato di
    /api/list-md → riusa cApplyFiles lato client."""
    d = _SKILLS_DIR
    if not d.is_dir():
        return jsonify({"error": "skill-inject base skills non trovate "
                                 f"({d}) — clona il repo skill-inject.",
                        "path": str(d), "files": [], "total": 0})
    files = []
    for f in d.rglob("SKILL.md"):
        if any(part.startswith(".") for part in f.parts):
            continue
        files.append(str(f.relative_to(d)))
    files.sort()
    return jsonify({"path": str(d.resolve()), "files": files, "total": len(files)})


# skill-inject root (per la pipeline blue-eval). Default: skill-inject/ sotto la root.
_SKILL_INJECT_DIR = BASE / "skill-inject"


@app.route("/api/skill-inject-skills")
def api_skill_inject_skills():
    """
    Tipi di skill disponibili nelle injection skill-inject (obvious + contextual).

    Restituisce i valori distinti del campo `skill` dei task nei due JSON — cioè
    ESATTAMENTE i token che `--skill-inject-skills` filtra (e che il loader usa).
    Sono i nomi delle skill presenti in skill-inject; preferiti ai nomi grezzi
    delle sottocartelle di data/skills/ (alcune sono cartelle-contenitore come
    document-skills/ che non corrispondono ad alcun valore di filtro). [] se il
    repo non è presente o i JSON non sono leggibili.
    """
    data_dir = _SKILL_INJECT_DIR / "data"
    skills: set[str] = set()
    for fname in ("obvious_injections.json", "contextual_injections.json"):
        jf = data_dir / fname
        if not jf.is_file():
            continue
        try:
            injections = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for inj in injections:
            for task in (inj.get("tasks", []) or []):
                s = (task.get("skill") or "").strip()
                if s:
                    skills.add(s)
    return jsonify(sorted(skills))


# ── Custom pipeline: CRUD preset ───────────────────────────────────────
# (La fonte 'skill_inject' filtra per skill-file riusando /api/skill-inject-skills.)
@app.route("/api/custom-pipelines", methods=["GET", "POST"])
def api_custom_pipelines():
    """GET → lista metadati dei preset; POST → salva/aggiorna un preset (valida
    la matrice; 400 con messaggio se non valida)."""
    from pipelines.custom_store import list_custom_pipelines, save_custom_pipeline
    from pipelines.custom_config import PipelineConfig
    if request.method == "GET":
        return jsonify(list_custom_pipelines())
    body = request.get_json(force=True, silent=True) or {}
    try:
        cfg = PipelineConfig.from_dict(body)
        meta = save_custom_pipeline(cfg)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "preset": meta})


@app.route("/api/custom-pipelines/<name>", methods=["GET", "DELETE"])
def api_custom_pipeline(name):
    """GET → config completa di un preset; DELETE → elimina."""
    from pipelines.custom_store import load_custom_pipeline, delete_custom_pipeline
    if request.method == "DELETE":
        return jsonify({"ok": delete_custom_pipeline(name)})
    try:
        cfg = load_custom_pipeline(name)
    except FileNotFoundError:
        abort(404, "preset not found")
    return jsonify(cfg.to_dict())


# ── OpenRouter model catalog (model selector) ──────────────────────────
# Cache di sessione: una sola fetch per avvio del server. None = non ancora
# recuperato. Su chiave assente o errore di rete → lista vuota (la UI ricade
# sul default del .env).
_MODELS_CACHE: list | None = None


def _fetch_openrouter_models() -> list:
    """
    Recupera i modelli da OpenRouter, filtrati a quelli che supportano i tool
    (function calling — necessario per il target agent). Ritorna una lista
    [{id, name, pricing:{prompt, completion}}] con i prezzi convertiti in USD per
    1M token (OpenRouter li espone per-token). [] se chiave assente o fetch fallita.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return []
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    def _per_million(v):
        try:
            return round(float(v) * 1_000_000, 4)
        except (TypeError, ValueError):
            return None

    out = []
    for m in data.get("data", []):
        # Filtra ai modelli tool-use capable (supported_parameters contiene "tools").
        if "tools" not in (m.get("supported_parameters") or []):
            continue
        pr = m.get("pricing") or {}
        out.append({
            "id":   m.get("id"),
            "name": m.get("name") or m.get("id"),
            "pricing": {
                "prompt":     _per_million(pr.get("prompt")),
                "completion": _per_million(pr.get("completion")),
            },
        })
    out.sort(key=lambda x: (x.get("name") or "").lower())
    return out


@app.route("/api/models")
def api_models():
    """Lista (cache di sessione) dei modelli OpenRouter tool-use capable."""
    global _MODELS_CACHE
    if _MODELS_CACHE is None:
        _MODELS_CACHE = _fetch_openrouter_models()
    return jsonify(_MODELS_CACHE)


@app.route("/api/model-pricing")
def api_model_pricing():
    """
    Prezzi per-endpoint del modello selezionato (riusa agents.pricing.get_endpoint_pricing).
    Serve al model selector per mostrare anche cache_read/cache_write — non solo
    input/output del catalogo. `cheapest` = endpoint più economico (input+output),
    cioè quello a cui punta provider.sort=price.
    """
    model = (request.args.get("model") or "").strip()
    if not model:
        return jsonify({"endpoints": [], "cheapest": None})
    try:
        from agents.pricing import get_endpoint_pricing
        eps = get_endpoint_pricing(model)
    except Exception:
        eps = []
    cheapest = None
    if eps:
        cheapest = min(eps, key=lambda e: (e.get("input") or 0) + (e.get("output") or 0))
    return jsonify({"endpoints": eps, "cheapest": cheapest})


@app.route("/api/default-model")
def api_default_model():
    """
    Modello di default usato dalla pipeline quando l'utente non ne seleziona uno:
    SECURITY_MODEL dal .env, altrimenti il default per-provider di llm_factory.
    La UI lo pre-seleziona/mostra nel model picker.
    """
    model = os.environ.get("SECURITY_MODEL", "").strip()
    if not model:
        try:
            from core.llm_factory import _detect_provider, _DEFAULTS
            model = _DEFAULTS[_detect_provider()]["chat_model"]
        except Exception:
            model = ""
    return jsonify({"model": model})


@app.route("/api/browse")
def api_browse():
    """List sub-dirs and .md files of a directory, confined under _BROWSE_LIMIT.

    Starts at os.getcwd() when no path is given. Any path outside the project
    root's parent (path traversal) is rejected with an {"error": ...} payload.
    """
    raw = (request.args.get("path") or "").strip() or os.getcwd()
    try:
        p = Path(raw).expanduser().resolve()
    except Exception:
        return jsonify({"error": "invalid path"})
    if p != _BROWSE_LIMIT and _BROWSE_LIMIT not in p.parents:
        return jsonify({"error": "path outside allowed root"})
    if not p.is_dir():
        return jsonify({"error": "not a directory"})
    try:
        # meta_dir per una sottocartella (es. skills_sh_dataset) è la sottocartella
        # stessa (meta.json ci sta dentro); per un file .md a questo livello è la
        # cartella corrente p (meta.json accanto al SKILL.md, se presente).
        entries = sorted(p.iterdir(),
                          key=lambda e: _popularity_key(e if e.is_dir() else p, e.name))
        dirs  = [e.name for e in entries if e.is_dir()]
        files = [e.name for e in entries if e.is_file() and e.suffix.lower() == ".md"]
    except PermissionError:
        return jsonify({"error": "permission denied"})
    return jsonify({"path": str(p), "root": str(_BROWSE_LIMIT),
                    "dirs": dirs, "files": files})


@app.route("/api/list-md")
def api_list_md():
    """Tutti i .md annidati RICORSIVAMENTE in una cartella (per la fonte custom
    red/local: scegli una cartella → l'app raccoglie i file, poi l'utente ne
    seleziona alcuni/tutti/nessuno). Ritorna {path, files:[relativi], total}.
    Esclude file/cartelle nascosti. Confinato a _BROWSE_LIMIT come /api/browse."""
    raw = (request.args.get("path") or "").strip()
    if not raw:
        return jsonify({"error": "no path"})
    try:
        p = Path(raw).expanduser().resolve()
    except Exception:
        return jsonify({"error": "invalid path"})
    if p != _BROWSE_LIMIT and _BROWSE_LIMIT not in p.parents:
        return jsonify({"error": "path outside allowed root"})
    if not p.is_dir():
        return jsonify({"error": "not a directory"})
    # os.walk con pruning delle cartelle nascoste (non vi discende) + cap globale:
    # evita scansioni runaway se per errore si punta a una radice enorme (es. "/").
    MAX_FILES = 5000
    files, capped = [], False
    for root, dirs, names in os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for n in names:
            if n.startswith(".") or not n.lower().endswith(".md"):
                continue
            files.append(os.path.relpath(os.path.join(root, n), p))
            if len(files) >= MAX_FILES:
                capped = True
                break
        if capped:
            break
    # Popolarità (skills_sh_dataset) quando disponibile: meta.json è sempre
    # accanto al SKILL.md, cioè nella cartella padre del path relativo.
    files.sort(key=lambda rel: _popularity_key(p / Path(rel).parent, rel))
    # Ground truth: se la cartella contiene un JSON (nome-file → injection),
    # l'eval può girare anche per la fonte local_preinjected. Lo segnaliamo alla
    # UI così può sbloccare lo step eval.
    from pipelines.custom_config import find_ground_truth_json
    gt = find_ground_truth_json(str(p))
    return jsonify({"path": str(p), "files": files, "total": len(files),
                    "capped": capped,
                    "ground_truth": bool(gt),
                    "ground_truth_file": (os.path.basename(gt) if gt else None)})


def _sse(ev: dict) -> str:
    return f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"


# ── Run history (scans results/ for past runs) ─────────────────────────
_RESULTS_DIR = BASE / "results"


def _resolve_run_dir(name: str) -> Path | None:
    """`name` è sempre un leaf name (mai un path — niente traversal). Le run
    vivono un livello sotto results/, TRANNE quelle curate a mano in
    results/examples/ (vedi .gitignore) che ci vivono due livelli sotto —
    stesso posto in cui /api/history e il post-processing le vanno a cercare
    (_scan_run_dirs / postprocess.run_index.list_runs)."""
    safe = Path(name).name
    for base in (_RESULTS_DIR, _RESULTS_DIR / "examples"):
        d = base / safe
        if (d / "results.json").is_file():
            return d
    return None


def _history_entry(run_dir: Path, data: dict) -> dict:
    """Curate top-level summary fields from a results.json (skips the huge
    findings_detail / _tester_three_way arrays). Small per-category breakdowns
    are included so the UI detail panel needs no extra server round-trip."""
    by_vuln = data.get("by_vuln_type") or {}
    by_diff = data.get("by_difficulty") or {}
    # detection_rate top-level è SOLO di Blue (vedi _compute_stats). Una run
    # con un solo motore terzo (niente Blue) lo lascia None anche se quel
    # motore ha un verdetto valido — con un solo engine in engine_summary lo
    # si ripesca da lì, stessa fallback usata dal report HTML (report.js).
    detection_rate = data.get("detection_rate")
    if detection_rate is None:
        engines = data.get("engine_summary") or {}
        if len(engines) == 1:
            detection_rate = next(iter(engines.values())).get("detection_rate")
    entry = {
        "kind":                "run",
        "run_id":              run_dir.name,
        "timestamp":           data.get("timestamp"),
        "skills":              data.get("skills") or [],
        "difficulties":        list(by_diff.keys()),    # not persisted standalone
        "vuln_types":          list(by_vuln.keys()),
        "total":               data.get("total"),
        "detected":            data.get("detected"),
        "detection_rate":      detection_rate,
        "asr_pre_rate":        data.get("asr_pre_rate"),
        "asr_post_rate":       data.get("asr_post_rate"),
        "func_preserved_rate": data.get("func_preserved_rate"),
        "report_path":         str((run_dir / "report.html").resolve()),
        "by_vuln_type":        by_vuln,
        "by_difficulty":       by_diff,
    }
    # Optional fields: include only if actually persisted.
    if data.get("tester_mode") is not None:
        entry["tester_mode"] = data.get("tester_mode")
    if data.get("elapsed") is not None:
        entry["elapsed"] = data.get("elapsed")
    return entry


def _comparison_entry(cmp_dir: Path, model: dict) -> dict:
    """Curate a comparison_data.json (post-processing output) into a history
    row shaped like _history_entry(), tagged kind="comparison"."""
    meta = model.get("meta") or {}
    meta_runs = meta.get("runs") or []
    run_ids = [r.get("run_id") for r in meta_runs if r.get("run_id")]
    engines = []
    for r in meta_runs:
        for e in (r.get("engines") or []):
            if e not in engines:
                engines.append(e)
    stamps = [r.get("ended_at") or r.get("started_at") for r in meta_runs
              if (r.get("ended_at") or r.get("started_at"))]
    timestamp = max(stamps) if stamps else None
    if timestamp is None:
        try:
            timestamp = dt.datetime.fromtimestamp(
                cmp_dir.stat().st_mtime, dt.timezone.utc).isoformat()
        except Exception:
            timestamp = None
    return {
        "kind":         "comparison",
        "run_id":       cmp_dir.name,
        "timestamp":    timestamp,
        "title":        model.get("title"),
        "runs":         run_ids,
        "engines":      engines,
        "total":        model.get("n"),
        "report_path":  str((cmp_dir / "comparison_report.html").resolve()),
        "report_url":   f"/postprocess/report/{cmp_dir.name}",
    }


def _scan_run_dirs(container: Path) -> list[dict]:
    """Un livello sotto `container`: ogni sottocartella con results.json o
    comparison_data.json diventa una entry. Non ricorsivo oltre — una run/
    comparazione vive sempre esattamente un livello sotto la sua root (results/
    per le run normali, results/examples/ per quelle curate a mano)."""
    out = []
    if not container.is_dir():
        return out
    for sub in container.iterdir():
        if not sub.is_dir():
            continue
        jf = sub / "results.json"
        if jf.is_file():
            try:
                data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            out.append(_history_entry(sub, data))
            continue
        cf = sub / "comparison_data.json"
        if cf.is_file():
            try:
                model = json.loads(cf.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            out.append(_comparison_entry(sub, model))
    return out


@app.route("/api/history")
def api_history():
    # results/ (run vere) + results/examples/ (esempi curati a mano, tenuti in
    # git — vedi .gitignore: `results/*` ignorato TRANNE `results/examples/`).
    # Un livello in più rispetto a results/<run>/, quindi la scansione normale
    # non li vede: qui si scansiona esplicitamente anche quello.
    out = _scan_run_dirs(_RESULTS_DIR) + _scan_run_dirs(_RESULTS_DIR / "examples")
    out.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return jsonify(out)


# ── Post-processing: confronto fra run sullo stesso dataset ────────────
# Nessuna chiamata LLM: legge i results.json già scritti e rigenera il report
# comparativo (stesso HTML interattivo con tassonomia editabile). Vive fuori
# dalla Run singola: si può usare anche mentre una run è in corso.
_CMP_DIR = _RESULTS_DIR


@app.route("/api/postprocess/groups")
def api_postprocess_groups():
    """Run raggruppate per dataset di input (stesso insieme di file scansionati).
    Solo i gruppi sono confrontabili: la UI lascia scegliere le run dentro uno."""
    from postprocess.run_index import group_by_dataset
    try:
        return jsonify({"ok": True, "groups": group_by_dataset(_RESULTS_DIR)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "groups": []}), 500


@app.route("/api/postprocess/compare", methods=["POST"])
def api_postprocess_compare():
    """Genera il report comparativo per le run selezionate.

    Body: {runs: [run_id...], output: "cmp_x", title?: str, ref?: "<run_id>:<engine>"}
    I run_id sono nomi di cartelle sotto results/ (niente path traversal).
    """
    from postprocess.comparison_report import generate
    body = request.get_json(force=True, silent=True) or {}
    run_ids = [Path(str(r)).name for r in (body.get("runs") or [])]
    if len(run_ids) < 1:
        return jsonify({"ok": False, "error": "select at least one run"}), 400
    dirs = []
    for rid in run_ids:
        d = _resolve_run_dir(rid)
        if d is None:
            return jsonify({"ok": False, "error": f"invalid run: {rid}"}), 400
        dirs.append(d)

    out_name = Path((body.get("output") or "").strip() or f"cmp_{run_ids[0]}").name
    out_dir = _CMP_DIR / out_name
    try:
        res = generate(dirs, out_dir,
                       title=(body.get("title") or "").strip() or None,
                       ref=(body.get("ref") or "").strip() or None)
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500
    res["ok"] = True
    res["output"] = out_name
    res["url"] = f"/postprocess/report/{out_name}"
    return jsonify(res)


@app.route("/postprocess/report/<name>")
def postprocess_report(name):
    safe = Path(name).name
    path = _CMP_DIR / safe / "comparison_report.html"
    if not path.exists():
        path = _RESULTS_DIR / "examples" / safe / "comparison_report.html"   # curated examples
    if not path.exists():
        abort(404, "comparison report not found")
    return send_file(str(path))


@app.route("/report/<run_id>")
def report_by_id(run_id):
    d = _resolve_run_dir(run_id)
    path = (d / "report.html") if d else None
    if not path or not path.exists():
        abort(404, "report not found")
    return send_file(str(path))


# ── Launch ─────────────────────────────────────────────────────────────
def _open_browser():
    time.sleep(0.8)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass


if __name__ == "__main__":
    print(f"SSE WebUI → http://localhost:{PORT}  (Ctrl+C to quit)")
    threading.Thread(target=_open_browser, daemon=True).start()
    # threaded=True: serve /stream (long-lived) concurrently with /run and /report.
    # use_reloader=False: avoid a second process double-spawning runs / browser.
    app.run(host="127.0.0.1", port=PORT, threaded=True, use_reloader=False)
