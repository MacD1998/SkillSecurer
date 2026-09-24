"""
core/cli_output.py — output CLI pulito e orientato al progresso per SSE.
Solo stdlib (sys, time, datetime, shutil, threading). Nessuna dipendenza esterna.

Layout (vedi spec):
  - HEADER: box adattivo (┌─┐) con "SkillSecurer · <data ora> · <scope>",
    poi righe indentate injections/attempts/parallel e vuln types a capo
    con rientro appeso sotto il primo nome.
  - FASI: una banner line `● [HH:MM:SS]  <name>  <desc>`; gli step completati
    sono righe `▸ N/total <label>` (newline, NO \r per red/blue/env); a fine
    fase `✓ done in Xs`.
  - TESTER: barra a riga singola che si riscrive con \r (solo tty); a fine
    fase un separatore tratteggiato.
  - FOOTER: box "SkillSecurer run complete · elapsed Xm Ys", stat aggregate,
    path report e una riga di sintesi per injection.
  - warn()/error() sempre visibili, su riga nuova, mai sovrascritte dalla barra.
  - Tutto il resto (tool call, trace, path, dettagli) passa per debug() ed è
    soppresso salvo SSE_VERBOSE=1.
Larghezze, allineamenti e durate (Xm Ys) sono calcolati dinamicamente.
"""
import os
import sys
import shutil
import threading
import time
from datetime import datetime

_VERBOSE = bool(os.environ.get("SSE_VERBOSE", "").strip())

# Rientro degli step (▸ / ✓) sotto la banner di fase.
_IND = " " * 12


def is_verbose() -> bool:
    return _VERBOSE

_run_start: float | None = None
_phase_start: float | None = None
_active = None   # Progress attiva (per pulire la riga prima di altri output)
_io_lock = threading.Lock()

# Buffer warning/error del run: ogni evento {level, msg, phase}. Serve a riportarli
# anche nel report finale (MD/HTML/PDF), non solo a terminale. Cap per evitare
# crescita illimitata su run lunghi (i conteggi restano comunque corretti).
_log_events: list[dict] = []
_LOG_EVENTS_CAP = 2000


def _record_event(level: str, msg: str) -> None:
    """Accoda un evento. Il CHIAMANTE deve già detenere _io_lock (lock non rientrante)."""
    if len(_log_events) < _LOG_EVENTS_CAP:
        _log_events.append({"level": level, "msg": str(msg), "phase": _current_phase})


def get_log_events() -> list[dict]:
    """Copia degli eventi warn/error accumulati nel run corrente."""
    with _io_lock:
        return list(_log_events)

# Durate per-fase (nome fase → secondi), in ordine d'esecuzione. Una fase si
# chiude — e la sua durata viene accumulata — via phase_done() OPPURE all'apertura
# della fase successiva: così anche la fase 'tester' (che non chiama phase_done,
# usa la Progress bar + separator) viene registrata quando parte 'report'.
_phase_times: dict[str, float] = {}
_current_phase: str | None = None


def _record_current_phase() -> None:
    """Accumula in _phase_times la durata della fase attualmente aperta (se c'è)."""
    global _current_phase
    if _current_phase is not None and _phase_start is not None:
        _phase_times[_current_phase] = (_phase_times.get(_current_phase, 0.0)
                                        + (time.time() - _phase_start))
    _current_phase = None


def get_phase_times() -> dict[str, float]:
    """Copia delle durate per-fase accumulate (secondi), in ordine d'esecuzione."""
    return dict(_phase_times)


# ── helpers ───────────────────────────────────────────────────────────
def _is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _cols() -> int:
    try:
        return shutil.get_terminal_size((80, 20)).columns
    except Exception:
        return 80


def _ts(t: float | None = None) -> str:
    return datetime.fromtimestamp(t or time.time()).strftime("%H:%M:%S")


def _hms(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"


def _clear_line():
    """Cancella la riga della progress bar attiva (solo tty)."""
    if _active is not None and _is_tty():
        sys.stdout.write("\r" + " " * (_active.width + 1) + "\r")
        sys.stdout.flush()


def _box(text: str) -> list[str]:
    """Box a larghezza adattiva attorno a una singola riga di testo."""
    cols   = max(20, _cols())
    max_in = cols - 2                   # spazio per i bordi │ │
    inner  = " " + text + " "
    if len(inner) > max_in:
        keep  = max(1, max_in - 2)      # 1 char per "…" + bordo
        inner = " " + text[:keep - 1] + "…"
    w = len(inner)
    return ["┌" + "─" * w + "┐",
            "│" + inner + "│",
            "└" + "─" * w + "┘"]


def _wrap_vuln(vuln_types: list[str]) -> list[str]:
    """Vuln types a capo con rientro appeso allineato sotto il primo nome."""
    prefix = "  vuln  "
    hang   = " " * len(prefix)
    cols   = max(40, _cols())
    sep    = "  "
    lines: list[str] = []
    cur     = prefix
    started = False
    for vt in vuln_types:
        if started and len(cur) + len(sep) + len(vt) > cols:
            lines.append(cur)
            cur = hang + vt
        else:
            cur += (sep + vt) if started else vt
        started = True
    if cur.strip():
        lines.append(cur)
    return lines


# ── output di base ────────────────────────────────────────────────────
def start_run():
    global _run_start, _current_phase
    _run_start = time.time()
    _phase_times.clear()       # reset per run (es. ri-esecuzioni dalla WebUI)
    _current_phase = None
    with _io_lock:
        _log_events.clear()    # reset eventi warn/error per il nuovo run


def debug(msg: str = "") -> None:
    if _VERBOSE:
        with _io_lock:
            _clear_line()
            print(msg, flush=True)
            if _active is not None:
                _active._redraw()


def info(msg: str = "") -> None:
    with _io_lock:
        _clear_line()
        print(msg, flush=True)
        if _active is not None:
            _active._redraw()


def warn(msg: str) -> None:
    with _io_lock:
        _clear_line()
        print(f"⚠  {msg}", flush=True)
        _record_event("warn", msg)
        if _active is not None:
            _active._redraw()


def error(msg: str) -> None:
    with _io_lock:
        _clear_line()
        print(f"✗  {msg}", flush=True)
        _record_event("error", msg)
        if _active is not None:
            _active._redraw()


# ── blocchi strutturati ───────────────────────────────────────────────
def header(scope: str, injections, attempts, parallel, vuln_types) -> None:
    global _run_start
    if _run_start is None:
        _run_start = time.time()
    dt    = datetime.fromtimestamp(_run_start).strftime("%Y-%m-%d %H:%M:%S")
    title = f"SkillSecurer  ·  {dt}" + (f"  ·  {scope}" if scope else "")
    with _io_lock:
        _clear_line()
        for ln in _box(title):
            print(ln, flush=True)
        print(f"  injections {injections}  ·  attempts {attempts}  ·  parallel {parallel}",
              flush=True)
        for ln in _wrap_vuln(list(vuln_types or [])):
            print(ln, flush=True)


def phase(name: str, desc: str = "") -> None:
    """Banner di fase: `● [HH:MM:SS]  <name>  <desc>`. Avvia il timer di fase."""
    global _phase_start, _current_phase
    _record_current_phase()    # chiude la fase precedente non ancora registrata
    _phase_start = time.time()
    _current_phase = name
    with _io_lock:
        _clear_line()
        print(f"\n● [{_ts()}]  {name.ljust(6)}  {desc}".rstrip(), flush=True)
        if _active is not None:
            _active._redraw()


def item(text: str, marker: str = "▸") -> None:
    """Riga di step indentata sotto la fase (newline, no \r)."""
    with _io_lock:
        _clear_line()
        print(f"{_IND}{marker} {text}".rstrip(), flush=True)
        if _active is not None:
            _active._redraw()


# Prefisso machine-readable per gli snapshot token live. Emesso SOLO sotto WebUI
# (gate SSE_EMIT_TOKENS): il WebUI lo intercetta e lo trasforma in evento SSE,
# NON lo mostra nel log umano. In terminale normale (no env) non viene mai emesso.
TOKENS_MARKER = "@@SSE_TOKENS@@"


_MODEL_CACHE: str | None = None


def _resolved_model() -> str:
    """Modello effettivamente in uso dalla pipeline: SECURITY_MODEL (impostata
    dal selector della WebUI, o dal .env) altrimenti il default per-provider di
    llm_factory — stessa risoluzione di benchmark.py per il campo `model` del
    report finale, così pannello live e report dicono la stessa cosa.
    Risolto una volta sola: l'env non cambia durante il run."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        model = os.environ.get("SECURITY_MODEL", "").strip()
        if not model:
            try:
                from core.llm_factory import _detect_provider, _DEFAULTS
                model = _DEFAULTS[_detect_provider()]["chat_model"]
            except Exception:
                model = ""
        _MODEL_CACHE = model
    return _MODEL_CACHE


def emit_token_usage(stats: dict, input_price=None, output_price=None) -> None:
    """
    Stampa una riga marker con lo snapshot token corrente (+ costo stimato) così
    il WebUI può mostrare costo/uso live, anche raggruppato per agente. No-op se
    SSE_EMIT_TOKENS non è impostata (così il CLI normale resta pulito).

    Oltre ai numeri il payload porta il CONTESTO del run (modello risolto,
    provider esclusi dal routing, origine del costo): senza, il pannello live
    mostrava cifre senza dire a quale modello/provider si riferissero.
    """
    if not os.environ.get("SSE_EMIT_TOKENS"):
        return
    import json as _json
    # Preferisci il costo REALE fatturato (somma usage.cost da OpenRouter); ricadi
    # sulla stima --input-price/--output-price solo se il provider non lo riporta.
    real = stats.get("cost") or 0.0
    if real > 0:
        cost = round(real, 6)
        cost_source = "openrouter"          # costo reale fatturato
    elif input_price is not None or output_price is not None:
        c = 0.0
        if input_price:
            c += stats.get("input_tokens", 0) / 1_000_000 * float(input_price)
        if output_price:
            c += stats.get("output_tokens", 0) / 1_000_000 * float(output_price)
        cost = round(c, 4)
        cost_source = "estimate"
    else:
        cost = None
        cost_source = None
    payload = {
        "model":              _resolved_model(),
        "cost_source":        cost_source,
        # Provider esclusi dal routing OpenRouter (checkbox della WebUI →
        # OPENROUTER_PROVIDER_IGNORE, vedi llm_factory/llm_proxy).
        "provider_ignore":    [p.strip() for p in
                               os.environ.get("OPENROUTER_PROVIDER_IGNORE", "").split(",")
                               if p.strip()],
        "input_tokens":       stats.get("input_tokens", 0),
        "output_tokens":      stats.get("output_tokens", 0),
        "total_tokens":       stats.get("total_tokens", 0),
        "cache_read_tokens":  stats.get("cache_read_tokens", 0),
        "cache_write_tokens": stats.get("cache_write_tokens", 0),
        "calls":              stats.get("calls", 0),
        "estimated_cost_usd": cost,
        "providers":          stats.get("providers", {}),
        "by_agent":           stats.get("by_agent", {}),
    }
    with _io_lock:
        _clear_line()
        print(TOKENS_MARKER + _json.dumps(payload, ensure_ascii=False), flush=True)
        if _active is not None:
            _active._redraw()


def phase_done(timed: bool = True, text: str = "done") -> None:
    """Chiusura di fase: `✓ done in Xs` (o solo `✓ done` se timed=False)."""
    with _io_lock:
        _clear_line()
        if timed and _phase_start is not None:
            msg = f"{text} in {_hms(time.time() - _phase_start)}"
        else:
            msg = text
        print(f"{_IND}✓ {msg}", flush=True)
        if _active is not None:
            _active._redraw()
    _record_current_phase()    # registra la durata della fase appena conclusa


def separator() -> None:
    """Separatore tratteggiato a larghezza terminale (post barra tester)."""
    cols = max(20, _cols())
    line = "  " + "─ " * ((cols - 2) // 2)
    with _io_lock:
        _clear_line()
        print(line.rstrip(), flush=True)
        if _active is not None:
            _active._redraw()


def _fmt_tok(n) -> str:
    """1234567 → '1.2M', 3456 → '0.3M' è troppo grezzo; usa K/M con 1 decimale."""
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def footer(report_path, total, detected, asr_pre, asr_post, rows=None, tokens=None,
           labels=None) -> None:
    """
    Box di chiusura + stat aggregate + path report + una riga per injection.
    rows: lista di tuple (label, detected_bool, asr_pre, asr_post,
          base_pass, n, fixed_state) con fixed_state ∈ {"✓","✗","skip"}.
    tokens: dict token_usage ({input_tokens, output_tokens, estimated_cost_usd})
            — se presente, stampa una riga "Tokens: ... | Est. cost: ...".
    labels: override opzionale delle etichette della riga riassuntiva, es.
            {"detected": "caught", "asr_pre": "detection", "asr_post": "precision"}
            — usato dalla pipeline blue-eval che non parla di ASR.
    """
    lbl = {"detected": "detected", "asr_pre": "ASR pre", "asr_post": "ASR post"}
    if labels:
        lbl.update(labels)
    end     = time.time()
    elapsed = end - (_run_start or end)
    title   = f"SkillSecurer run complete  ·  elapsed {_hms(elapsed)}"
    with _io_lock:
        _clear_line()
        for ln in _box(title):
            print(ln, flush=True)
        print(f"  injections {total}  ·  {lbl['detected']} {detected}  ·  "
              f"{lbl['asr_pre']} {asr_pre}  ·  {lbl['asr_post']} {asr_post}", flush=True)
        if tokens:
            line = (f"  Tokens: {_fmt_tok(tokens.get('input_tokens'))} input  "
                    f"{_fmt_tok(tokens.get('output_tokens'))} output")
            _cost = tokens.get("estimated_cost_usd")
            if _cost is not None:
                line += f"  |  Est. cost: ${float(_cost):.2f}"
            print(line, flush=True)
        if report_path:
            print(f"  report  {report_path}", flush=True)
        if rows:
            print("", flush=True)
            w = max((len(r[0]) for r in rows), default=0)
            for (label, det, pre, post, base_pass, n, fstate) in rows:
                dmark = "✓" if det else "✗"
                fdisp = {"✓": "fixed ✓", "✗": "fixed ✗",
                         "skip": "fixed skip"}.get(fstate, f"fixed {fstate}")
                print(f"  {label.ljust(w)}  detect {dmark}  asr {pre}→{post}  "
                      f"base {base_pass}/{n}  {fdisp}", flush=True)


# ── progress bar (solo tester) ────────────────────────────────────────
class Progress:
    """
    Barra di avanzamento a riga singola. In tty si riscrive con \r; in pipe
    non emette nulla (per non spammare) — restano header/fasi/footer.
    Thread-safe: aggiornabile dai worker paralleli del tester.
    Formato: `  [████████░░░░] 37/45  <label>`
    """
    def __init__(self, total: int = 1, label: str = ""):
        global _active
        self.total  = max(1, int(total))
        self.done   = 0
        self.label  = label
        self.width  = 0
        self._lock  = threading.Lock()
        _active = self
        # Disegna subito 0/total: progresso visibile dall'inizio.
        self.update()

    def _bar(self, frac: float, n: int = 20) -> str:
        filled = max(0, min(n, int(frac * n)))
        return "█" * filled + "░" * (n - filled)

    def _redraw(self) -> None:
        # Assume il chiamante tenga _io_lock; ridisegna la barra (solo tty).
        if not _is_tty():
            return
        frac = min(1.0, self.done / self.total)
        line = (f"  [{self._bar(frac)}] {self.done}/{self.total}"
                + (f"  {self.label}" if self.label else ""))
        self.width = max(self.width, len(line))
        sys.stdout.write("\r" + line + " " * (self.width - len(line)))
        sys.stdout.flush()

    def update(self, done: int | None = None, label: str | None = None) -> None:
        with _io_lock:
            with self._lock:
                if done is not None:  self.done  = done
                if label is not None: self.label = label
            self._redraw()

    def advance(self, label: str | None = None) -> None:
        with _io_lock:
            with self._lock:
                self.done += 1
                if label is not None:
                    self.label = label
            self._redraw()

    def finish(self) -> None:
        global _active
        with _io_lock:
            with self._lock:
                self.done = self.total
            self._redraw()
            if _is_tty():
                sys.stdout.write("\n")
                sys.stdout.flush()
            _active = None
