"""
llm_proxy.py — reverse proxy locale per i motori LLM esterni (skillspector/cisco/aig)
========================================================================================
SkillSpector/Cisco/aig-skill-scan girano come SUBPROCESSO ESTERNO (uvx / uv run —
vedi agents/skillspector_scanner.py, agents/cisco_scanner.py, agents/aig_scanner.py):
le loro chiamate LLM non passano da llm_factory.build_llm, quindi
TokenTrackingCallback (token_tracker.py) non le vede — token/costo reali erano
invisibili per costruzione. benchmark.py copriva il buco con una STIMA grezza
(costo medio/chiamata del Blue × n scan con used_llm=True), ora rimossa.

Fix: i tre tool accettano tutti un BASE_URL OpenAI-compatible configurabile
(rispettivamente OPENAI_BASE_URL, SKILL_SCANNER_LLM_BASE_URL, LLM_BASE_URL).
Puntandoli qui invece che a openrouter.ai/api/v1 direttamente, ogni loro
richiesta passa da questo processo: si inoltra a OpenRouter iniettando
usage.include=true + provider routing (stesso meccanismo di
llm_factory.py:170-188, stessi env var OPENROUTER_PROVIDER_SORT/ONLY/IGNORE)
e si legge cost/token REALI dalla response, registrati in token_tracker sotto
il nome dell'agente — stessa precisione E stesso routing cheapest-provider di
Blue.

L'agente è identificato dal path (/<agent>/v1/...): i tre scanner passano il
loro BASE_URL così com'è ai rispettivi SDK/CLI, un path prefix è l'unico modo
di taggare la richiesta senza toccare il codice dei tool vendorizzati/esterni.

Un solo server per l'intero run (ThreadingHTTPServer, thread-safe — record() di
token_tracker è già lockato): avviato da main.py prima di dispatchare la
pipeline, mai fermato esplicitamente in caso di crash (thread daemon, muore con
il processo). Se l'avvio fallisce (porta esaurita, ecc.) i tre scanner ricadono
su openrouter.ai diretto via base_url() → None: degrado SOLO
nell'osservabilità (si perde il tracking reale), mai nella funzionalità dello
scan.
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

import core.token_tracker as token_tracker

# NB: senza /v1 finale — i client OpenAI-compatible dei tre scanner appendono
# già "/v1/..." al loro BASE_URL (che qui è .../<agent>/v1, vedi base_url()),
# quindi il path in arrivo dopo aver tolto il prefisso <agent> è già "/v1/...".
UPSTREAM = "https://openrouter.ai/api"
VALID_AGENTS = ("skillspector", "cisco", "aig")

_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None
_port: int | None = None
_lock = threading.Lock()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silenzia il log di default (va su stderr ad ogni richiesta)
        pass

    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def _forward(self):
        parts = self.path.lstrip("/").split("/", 1)
        agent = parts[0] if parts else ""
        rest = "/" + parts[1] if len(parts) > 1 else ""
        if agent not in VALID_AGENTS:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        # Inietta usage.include=true + provider routing (stesso schema/env var di
        # llm_factory.py:170-188, usato per Blue/Red/Tester/Judge) così anche i
        # tool esterni ottengono cost/token reali E il routing cheapest-provider,
        # invece del default quality-first di OpenRouter.
        if body:
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = None
            if isinstance(payload, dict):
                usage = payload.get("usage")
                if not isinstance(usage, dict):
                    usage = {}
                usage["include"] = True
                payload["usage"] = usage

                prov_obj = payload.get("provider")
                if not isinstance(prov_obj, dict):
                    prov_obj = {}
                sort = os.environ.get("OPENROUTER_PROVIDER_SORT", "price").strip().lower()
                if sort and sort != "none":
                    prov_obj.setdefault("sort", sort)

                def _csv(env: str) -> list:
                    return [p.strip() for p in os.environ.get(env, "").split(",") if p.strip()]

                only = _csv("OPENROUTER_PROVIDER_ONLY")
                ignore = _csv("OPENROUTER_PROVIDER_IGNORE")
                if only:
                    prov_obj.setdefault("only", only)
                if ignore:
                    prov_obj.setdefault("ignore", ignore)
                if prov_obj:
                    payload["provider"] = prov_obj

                body = json.dumps(payload).encode("utf-8")

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in ("host", "content-length")}

        try:
            resp = httpx.request(self.command, UPSTREAM + rest, content=body,
                                  headers=headers, timeout=120.0)
        except httpx.HTTPError as e:
            err = f"llm_proxy: upstream error: {e}".encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)
            return

        ctype = resp.headers.get("content-type", "")
        if ctype.startswith("application/json"):
            try:
                _record(agent, resp.json())
            except (json.JSONDecodeError, ValueError):
                pass
        elif "text/event-stream" in ctype:
            # aig-skill-scan chiama in streaming (stream=True + stream_options.
            # include_usage — vedi skill_scan/utils/llm.py del pacchetto): la
            # response è SSE, non un singolo JSON. httpx.request() la bufferizza
            # comunque per intero (nessuna vera relay in tempo reale, qui non
            # serve): si legge il chunk finale (quello con "usage" popolato,
            # scelte vuote) dal testo bufferizzato.
            _record_sse(agent, resp.text)

        self.send_response(resp.status_code)
        skip = ("content-length", "transfer-encoding", "content-encoding", "connection")
        for k, v in resp.headers.items():
            if k.lower() in skip:
                continue
            self.send_header(k, v)
        content = resp.content
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def _record_sse(agent: str, text: str) -> None:
    """Estrae l'usage dal chunk SSE finale (`data: {...}` con "usage" popolato —
    gli altri chunk di delta hanno "usage": null). Se più chunk portano usage
    (non dovrebbe succedere, ma non ci si affida all'ordine) li registra tutti:
    _record somma, mai sovrascrive, quindi un doppio "usage" popolato
    gonfierebbe il conteggio — rischio accettato, l'API OpenRouter/OpenAI
    manda l'usage in un solo chunk finale per costruzione dello streaming."""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("usage"):
            _record(agent, obj)


def _record(agent: str, data: dict) -> None:
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return
    input_tokens  = int(usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or 0)
    ptd = usage.get("prompt_tokens_details") or {}
    cache_read = int((ptd or {}).get("cached_tokens") or 0)
    ctd = usage.get("completion_tokens_details") or {}
    reasoning = int((ctd or {}).get("reasoning_tokens") or 0)
    cache_write = int(usage.get("cache_write_tokens") or 0)
    try:
        cost = float(usage.get("cost") or 0.0)
    except (TypeError, ValueError):
        cost = 0.0
    provider = data.get("provider") if isinstance(data, dict) else None
    if input_tokens or output_tokens or cost:
        token_tracker.record(agent, input_tokens, output_tokens, calls=1,
                              cache_read_tokens=cache_read, cache_write_tokens=cache_write,
                              reasoning_tokens=reasoning, cost=cost, provider=provider)


def start() -> bool:
    """Avvia il proxy su una porta libera di 127.0.0.1 (no-op se già attivo).
    Ritorna False se l'avvio fallisce — i chiamanti ricadono su openrouter.ai
    diretto via base_url() → None, nessuna eccezione propagata."""
    global _server, _thread, _port
    with _lock:
        if _server is not None:
            return True
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        except OSError:
            return False
        _server = server
        _port = server.server_address[1]
        _thread = threading.Thread(target=server.serve_forever, daemon=True)
        _thread.start()
        return True


def stop() -> None:
    global _server, _thread, _port
    with _lock:
        if _server is not None:
            _server.shutdown()
            _server.server_close()
        _server = None
        _thread = None
        _port = None


def base_url(agent: str) -> str | None:
    """BASE_URL da passare allo scanner esterno per l'agente dato, o None se il
    proxy non è (ancora) attivo — i chiamanti ricadono su openrouter.ai diretto."""
    with _lock:
        port = _port
    if port is None or agent not in VALID_AGENTS:
        return None
    return f"http://127.0.0.1:{port}/{agent}/v1"
