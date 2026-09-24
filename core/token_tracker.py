"""
core/token_tracker.py — accumulatore globale thread-safe di token e costo LLM
========================================================================
Traccia l'uso di token (input/output) e il numero di chiamate LLM attraverso
l'intera pipeline SSE3, suddiviso per agente.

Due punti di ingresso:
  1. TokenTrackingCallback — callback LangChain agganciato da llm_factory.build_llm
     a OGNI client. Ogni agente passa il proprio nome (red/blue/judge/env/
     tester_judge) → on_llm_end estrae l'usage dalla risposta e lo
     somma all'accumulatore sotto quel nome.
  2. record() — usato direttamente per il target agent (gira in Docker e non passa
     da LangChain): il tester legge /workspace/.token_usage e chiama record(
     "target_agent", ...).

Tutti i contatori sono protetti da un lock: red/blue/tester girano in thread pool.

Stima costo: estimate_cost(input_price, output_price) con prezzi per 1M token.
None se nessun prezzo è fornito.
"""
from __future__ import annotations

import copy
import threading
import time

# Agenti noti — pre-seminati così l'ordine nei report è stabile anche se un
# agente non emette chiamate. by_agent accetta comunque chiavi extra (setdefault).
_KNOWN_AGENTS = ["red", "blue", "judge", "env", "tester_judge", "target_agent",
                 "skillspector", "cisco", "aig"]

_lock = threading.Lock()


def _empty() -> dict:
    # cache_read/cache_write restano colonne distinte: NON vengono ripiegate in
    # input_tokens. cost = USD realmente fatturato (usage.cost di OpenRouter),
    # 0.0 finché nessuna risposta lo riporta (→ fallback stima da prezzi).
    # reasoning_tokens = sottoinsieme degli output dedicato al ragionamento
    # (modelli reasoning); il loro costo è approssimato a parte (vedi usage_with_cost).
    # providers = breakdown {nome_provider: n_chiamate} dell'endpoint OpenRouter
    # che ha servito ciascuna chiamata (>1 voce ⇒ è entrato in gioco il fallback).
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "reasoning_tokens": 0, "cost": 0.0, "calls": 0, "providers": {}}


_stats: dict = {
    **_empty(),
    "by_agent": {a: _empty() for a in _KNOWN_AGENTS},
}


# ── Live emitter (snapshot push durante il run) ───────────────────────
# Permette di pubblicare snapshot parziali "time by time" (es. al WebUI via una
# riga marker su stdout). L'emitter è registrato dal caller; record() lo chiama
# in modo throttled così non spamma a ogni singola risposta LLM.
_emitter = None
_emit_interval = 1.2
_last_emit = 0.0

# Heartbeat: forza un emit ogni _heartbeat_interval secondi A PRESCINDERE da
# record(). Senza, il pannello live restava fermo per l'intera durata di fasi
# che non chiamano record() spesso — uno scan skillspector/cisco/aig fa UNA
# chiamata LLM a fine scan (dopo risoluzione ambiente uvx + analisi statica),
# un target agent gira in Docker fuori dal ciclo di record() dei client
# LangChain: minuti di silenzio in cui la WebUI sembrava bloccata, anche a run
# in corso. Thread daemon: muore con il processo, un solo run per processo
# (main.py è rilanciato come subprocess ad ogni run della WebUI) quindi non
# serve stoppare esplicitamente il precedente.
_heartbeat_interval = 3.0
_heartbeat_stop: threading.Event | None = None


def set_emitter(fn, interval: float = 1.2, heartbeat: float = 3.0) -> None:
    """Registra una funzione fn(snapshot: dict) chiamata (throttled) a ogni record(),
    più un emit forzato ogni `heartbeat` secondi anche senza nuove chiamate LLM."""
    global _emitter, _emit_interval, _heartbeat_interval, _heartbeat_stop
    _emitter = fn
    _emit_interval = max(0.0, float(interval))
    _heartbeat_interval = max(0.5, float(heartbeat))

    if _heartbeat_stop is not None:
        _heartbeat_stop.set()   # ferma un eventuale heartbeat precedente
    stop = threading.Event()
    _heartbeat_stop = stop

    def _loop():
        while not stop.wait(_heartbeat_interval):
            _maybe_emit(force=True)

    threading.Thread(target=_loop, daemon=True).start()


def _maybe_emit(force: bool = False) -> None:
    """Chiama l'emitter con uno snapshot, rispettando il throttle (salvo force)."""
    global _last_emit
    fn = _emitter
    if fn is None:
        return
    now = time.time()
    with _lock:
        if not force and (now - _last_emit) < _emit_interval:
            return
        _last_emit = now
        snap = copy.deepcopy(_stats)
    try:
        fn(snap)
    except Exception:
        pass


def emit_now() -> None:
    """Forza un emit immediato dello snapshot corrente (es. a fine run)."""
    _maybe_emit(force=True)


def reset() -> None:
    """Azzera l'accumulatore (utile tra run multipli nello stesso processo, es. WebUI)."""
    global _stats, _last_emit
    with _lock:
        _stats = {**_empty(), "by_agent": {a: _empty() for a in _KNOWN_AGENTS}}
        _last_emit = 0.0


def record(agent: str, input_tokens: int, output_tokens: int, calls: int = 1,
           cache_read_tokens: int = 0, cache_write_tokens: int = 0,
           reasoning_tokens: int = 0, cost: float = 0.0,
           provider: str | None = None, providers: dict | None = None) -> None:
    """Somma l'uso di token (+ cache + reasoning + costo reale) all'accumulatore
    globale e al bucket dell'agente.

    cache_read_tokens/cache_write_tokens restano colonne distinte (non confluiscono
    in input_tokens). reasoning_tokens è un sottoinsieme degli output_tokens (NON
    sommato a parte nel total). cost è il costo REALE fatturato (usage.cost di
    OpenRouter); 0.0 quando il provider non lo riporta.

    provider è il nome dell'endpoint OpenRouter che ha servito QUESTA singola
    chiamata (None se ignoto): viene accumulato nel breakdown providers
    {nome: n_chiamate}, incrementato di `calls`. Usato da llm_proxy (una
    risposta = una chiamata).

    providers è un breakdown GIA' AGGREGATO {nome: n_chiamate} — per chi
    riassume più chiamate in un solo record() (es. il target agent: N turni
    ReAct in un container, ognuno potenzialmente su un provider diverso sotto
    OPENROUTER_PROVIDER_SORT=price). Sommato direttamente, SENZA moltiplicare
    per `calls` (i conteggi sono già quelli giusti). provider/providers sono
    mutuamente esclusivi; se entrambi sono dati vince providers.
    """
    ti = int(input_tokens or 0)
    to = int(output_tokens or 0)
    cr = int(cache_read_tokens or 0)
    cw = int(cache_write_tokens or 0)
    rt = int(reasoning_tokens or 0)
    nc = int(calls or 0)
    try:
        co = float(cost or 0.0)
    except (TypeError, ValueError):
        co = 0.0
    prov = (str(provider).strip() or None) if provider else None
    prov_breakdown = {str(k): int(v) for k, v in providers.items() if v} if providers else None

    def _bump_providers(d: dict) -> None:
        pv = d.setdefault("providers", {})
        if prov_breakdown:
            for name, n in prov_breakdown.items():
                pv[name] = pv.get(name, 0) + n
        elif prov:
            pv[prov] = pv.get(prov, 0) + (nc or 1)

    with _lock:
        _stats["input_tokens"]       += ti
        _stats["output_tokens"]      += to
        _stats["total_tokens"]       += ti + to
        _stats["cache_read_tokens"]  += cr
        _stats["cache_write_tokens"] += cw
        _stats["reasoning_tokens"]   += rt
        _stats["cost"]               += co
        _stats["calls"]              += nc
        _bump_providers(_stats)
        bucket = _stats["by_agent"].setdefault(agent, _empty())
        bucket["input_tokens"]       += ti
        bucket["output_tokens"]      += to
        bucket["total_tokens"]       += ti + to
        bucket["cache_read_tokens"]  += cr
        bucket["cache_write_tokens"] += cw
        bucket["reasoning_tokens"]   += rt
        bucket["cost"]               += co
        bucket["calls"]              += nc
        _bump_providers(bucket)
    _maybe_emit()


def snapshot() -> dict:
    """Copia profonda dello stato corrente (sicura da serializzare/mutare)."""
    with _lock:
        return copy.deepcopy(_stats)


def estimate_cost(input_price: float | None, output_price: float | None,
                  stats: dict | None = None) -> float | None:
    """
    Costo stimato in USD dati i prezzi per 1M token (input/output).
    Ritorna None se entrambi i prezzi sono None (nessuna stima richiesta).
    """
    if input_price is None and output_price is None:
        return None
    s = stats or snapshot()
    cost = 0.0
    if input_price:
        cost += s.get("input_tokens", 0) / 1_000_000 * float(input_price)
    if output_price:
        cost += s.get("output_tokens", 0) / 1_000_000 * float(output_price)
    return round(cost, 4)


def usage_with_cost(input_price: float | None, output_price: float | None) -> dict:
    """
    Snapshot completo + estimated_cost_usd, pronto per results.json.

    Preferisce il costo REALE fatturato (somma di usage.cost da OpenRouter,
    accumulato in s["cost"]); ricade sulla stima --input-price/--output-price solo
    quando il provider non riporta alcun costo. estimated_cost_usd = None se non c'è
    né costo reale né prezzi per la stima.

    NB: reasoning_tokens resta nello snapshot come valore grezzo (debug/log) ma NON
    è una metrica a sé: è un SOTTOINSIEME di output_tokens (semantica OpenAI/
    OpenRouter), già incluso in output e quindi nel costo — esporlo come voce
    separata lo conterebbe due volte. Per questo non c'è alcun reasoning_cost.
    """
    s = snapshot()
    real = s.get("cost") or 0.0
    if real > 0:
        s["estimated_cost_usd"] = round(real, 6)
        s["cost_source"] = "openrouter"          # costo reale fatturato
    else:
        est = estimate_cost(input_price, output_price, s)
        s["estimated_cost_usd"] = est
        s["cost_source"] = "estimate" if est is not None else None
    return s


# ── Estrazione usage da una risposta LangChain ────────────────────────

def _as_dict(obj):
    """Normalizza a dict un oggetto usage che può essere dict o modello pydantic
    (es. prompt_tokens_details dell'OpenAI SDK). {} se non interpretabile."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    for attr in ("model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return getattr(obj, "__dict__", {}) or {}


def _merge_usage(res: dict, tu) -> None:
    """Estrae da un singolo blocco usage (OpenAI/OpenRouter-compatibile) tutti i
    campi e li somma in `res`. Tollera campi mancanti."""
    tu = _as_dict(tu)
    if not tu:
        return
    res["input_tokens"]  += int(tu.get("prompt_tokens") or tu.get("input_tokens") or 0)
    res["output_tokens"] += int(tu.get("completion_tokens") or tu.get("output_tokens") or 0)
    # cache_read: usage.prompt_tokens_details.cached_tokens (OpenRouter/OpenAI).
    ptd = _as_dict(tu.get("prompt_tokens_details") or tu.get("input_token_details"))
    res["cache_read_tokens"] += int(
        ptd.get("cached_tokens") or ptd.get("cache_read") or 0)
    # cache_write: campo OpenRouter-specifico (presente solo con alcuni provider).
    res["cache_write_tokens"] += int(tu.get("cache_write_tokens") or 0)
    # reasoning: usage.completion_tokens_details.reasoning_tokens (modelli reasoning).
    ctd = _as_dict(tu.get("completion_tokens_details") or tu.get("output_token_details"))
    res["reasoning_tokens"] += int(
        ctd.get("reasoning_tokens") or ctd.get("reasoning") or 0)
    # cost: USD realmente fatturato (usage.cost, abilitato da usage.include).
    try:
        c = tu.get("cost")
        if c is not None:
            res["cost"] += float(c)
    except (TypeError, ValueError):
        pass


def _extract_usage(response) -> dict:
    """
    Breakdown completo da un LLMResult LangChain:
    {input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost}.

    I campi OpenRouter-specifici (cost, prompt_tokens_details, cache_write_tokens)
    NON arrivano nella usage_metadata standard: vivono in llm_output['token_usage']
    / response_metadata della risposta grezza. Si legge da lì, con fallback su
    usage_metadata per i soli conteggi base.
    """
    res = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
           "cache_write_tokens": 0, "reasoning_tokens": 0, "cost": 0.0,
           "provider": None}

    # 1) llm_output['token_usage'] — aggregato per-call da ChatOpenAI, è la sede
    #    più ricca (include i campi extra di OpenRouter via model_extra).
    tu = None
    try:
        tu = (response.llm_output or {}).get("token_usage")
        # provider top-level OpenRouter (preservato da _ProviderAwareChatOpenAI).
        res["provider"] = (response.llm_output or {}).get("provider") or None
    except Exception:
        tu = None
    if tu:
        _merge_usage(res, tu)

    # 2) Se llm_output non portava nulla, leggi il response_metadata dei message.
    if res["input_tokens"] == 0 and res["output_tokens"] == 0 and res["cost"] == 0.0:
        try:
            for gen_list in (response.generations or []):
                for gen in gen_list:
                    msg = getattr(gen, "message", None)
                    rm  = getattr(msg, "response_metadata", None) if msg else None
                    if rm:
                        _merge_usage(res, rm.get("token_usage") or rm.get("usage"))
                        if not res["provider"]:
                            res["provider"] = rm.get("provider") or None
        except Exception:
            pass

    # 3) Ultimo fallback: usage_metadata (solo conteggi base + cache_read).
    if res["input_tokens"] == 0 and res["output_tokens"] == 0:
        try:
            for gen_list in (response.generations or []):
                for gen in gen_list:
                    msg = getattr(gen, "message", None)
                    um  = getattr(msg, "usage_metadata", None) if msg else None
                    if um:
                        res["input_tokens"]  += int(um.get("input_tokens") or 0)
                        res["output_tokens"] += int(um.get("output_tokens") or 0)
                        itd = _as_dict(um.get("input_token_details"))
                        res["cache_read_tokens"] += int(itd.get("cache_read") or 0)
                        otd = _as_dict(um.get("output_token_details"))
                        res["reasoning_tokens"]  += int(otd.get("reasoning") or 0)
        except Exception:
            pass
    return res


try:
    from langchain_core.callbacks import BaseCallbackHandler

    class TokenTrackingCallback(BaseCallbackHandler):
        """Callback agganciato a un client LLM: somma l'usage di ogni risposta
        all'accumulatore globale, taggandolo con il nome dell'agente."""

        def __init__(self, agent: str):
            self.agent = agent or "unknown"

        def on_llm_end(self, response, **kwargs):  # noqa: D401
            u = _extract_usage(response)
            if u["input_tokens"] or u["output_tokens"] or u["cost"]:
                record(self.agent, u["input_tokens"], u["output_tokens"], calls=1,
                       cache_read_tokens=u["cache_read_tokens"],
                       cache_write_tokens=u["cache_write_tokens"],
                       reasoning_tokens=u["reasoning_tokens"],
                       cost=u["cost"], provider=u["provider"])

except Exception:  # pragma: no cover — langchain non disponibile
    TokenTrackingCallback = None  # type: ignore
