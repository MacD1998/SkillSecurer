"""
core/llm_factory.py — factory condivisa per costruire client LLM
============================================================
Usato da tutti gli agenti SSE3 (red, blue, tester, judge, ecc.)
per evitare duplicazione e gestire più provider in modo uniforme.

Provider supportati:
  - deepseek      → https://api.deepseek.com/v1
  - openrouter    → https://openrouter.ai/api/v1
  - openai        → default OpenAI

Selezione del provider:
  1. Env var LLM_PROVIDER esplicita (deepseek | openrouter | openai)
  2. Auto-detect dalla presenza di API key

Env vars:
  - LLM_PROVIDER        (opzionale) — forza la scelta
  - DEEPSEEK_API_KEY    — API key DeepSeek
  - OPENROUTER_API_KEY  — API key OpenRouter
  - OPENAI_API_KEY      — API key OpenAI
  - SECURITY_MODEL      — modello di default per tutti gli agenti (fallback comune)

  Override per-agente (opzionali — se non impostati ricadono su SECURITY_MODEL):
  - RED_MODEL           — red (generazione injection)
  - BLUE_SCAN_MODEL     — blue, fase scan
  - BLUE_PATCH_MODEL    — blue, fase patch
  - TARGET_MODEL        — target agent (dentro il container Docker)
  - ENV_MODEL           — environment agent (setup di /workspace)
  - JUDGE_MODEL         — judge (verdetto bypass eseguito/no)
  - TESTER_MODEL        — tester_judge (generazione prompt + giudice task-completion)
  - VALIDATOR_MODEL     — verifier Tier-2 sui casi ambigui (blue_eval_judge)
"""
import os
from langchain_openai import ChatOpenAI


class _ProviderAwareChatOpenAI(ChatOpenAI):
    """ChatOpenAI che preserva il campo top-level ``provider`` della risposta
    OpenRouter (es. "DeepSeek", "StreamLake" — l'endpoint effettivamente scelto
    dal routing). langchain lo scarta: non finisce né in usage_metadata né in
    response_metadata. Qui lo ricopiamo in ``llm_output['provider']`` e nel
    ``response_metadata`` di ogni message, accanto a cost/cache, così il
    TokenTrackingCallback può attribuire ogni chiamata al provider che l'ha servita.
    Usata SOLO sul branch openrouter; del tutto trasparente (no-op) altrove."""

    def _create_chat_result(self, response, generation_info=None):
        result = super()._create_chat_result(response, generation_info)
        try:
            prov = (response.get("provider") if isinstance(response, dict)
                    else getattr(response, "provider", None))
            if prov:
                if result.llm_output is None:
                    result.llm_output = {}
                result.llm_output["provider"] = prov
                for gen in result.generations:
                    msg = getattr(gen, "message", None)
                    if msg is not None and hasattr(msg, "response_metadata"):
                        msg.response_metadata.setdefault("provider", prov)
        except Exception:
            pass
        return result


# Default per ogni provider
_DEFAULTS = {
    "deepseek": {
        "base_url":      "https://api.deepseek.com/v1",
        "chat_model":    "deepseek-chat",
        "reasoner_model":"deepseek-reasoner",
    },
    "openrouter": {
        "base_url":      "https://openrouter.ai/api/v1",
        "chat_model":    "deepseek/deepseek-v4-pro",   # default coerente con .env.example
        "reasoner_model":"anthropic/claude-3.5-sonnet",
    },
    "openai": {
        "base_url":      None,   # default OpenAI client
        "chat_model":    "gpt-4o-mini",
        "reasoner_model":"gpt-4o",
    },
}


def _detect_provider() -> str:
    """Determina il provider in base a env vars."""
    explicit = os.environ.get("LLM_PROVIDER", "").lower().strip()
    if explicit:
        if explicit not in _DEFAULTS:
            raise RuntimeError(f"LLM_PROVIDER non riconosciuto: {explicit!r}. "
                               f"Validi: {list(_DEFAULTS.keys())}")
        return explicit

    # Auto-detect
    if os.environ.get("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"

    raise RuntimeError(
        "Nessuna API key trovata. Imposta una di queste env vars: "
        "DEEPSEEK_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY"
    )


def _get_api_key(provider: str) -> str:
    """Ritorna l'API key per il provider, sollevando errore se vuota."""
    env_var = {
        "deepseek":   "DEEPSEEK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai":     "OPENAI_API_KEY",
    }[provider]
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise RuntimeError(f"API key {env_var} non trovata o vuota")
    return key


def build_llm(
    temp:           float = 0,
    model_env_var:  str | tuple[str, ...] | list[str] | None = None,
    fallback_model: str | None = None,
    agent:          str | None = None,
) -> ChatOpenAI:
    """
    Costruisce un client ChatOpenAI configurato per il provider rilevato.

    Args:
        temp:           temperatura del modello
        model_env_var:  env var (o tupla/lista di env var, controllate in ORDINE —
                        la prima non vuota vince) da cui leggere il nome del
                        modello. Il pattern standard per un override per-agente è
                        ("<RUOLO>_MODEL", "SECURITY_MODEL"): l'override specifico
                        vince se impostato, altrimenti si ricade sul modello
                        principale invece che sul default hardcoded per-provider.
        fallback_model: modello da usare se NESSUNA delle env var è definita
                        (None → usa il default per provider)
        agent:          nome dell'agente (red/blue/judge/env/tester_judge/...)
                        usato per taggare il consumo token nel token_tracker.
                        None → nessun tracking per questo client.

    Esempio:
        # Blue agent (scan e patch indipendentemente selezionabili, entrambi
        # ricadono su SECURITY_MODEL se il rispettivo override non è impostato)
        llm = build_llm(temp=0, model_env_var=("BLUE_SCAN_MODEL", "SECURITY_MODEL"), agent="blue")

        # Tester con modello custom
        llm = build_llm(temp=0.3, model_env_var=("TESTER_MODEL", "SECURITY_MODEL"), agent="tester_judge")
    """
    provider = _detect_provider()
    api_key  = _get_api_key(provider)
    defaults = _DEFAULTS[provider]

    # Risolve il modello: prima env var non vuota nell'ordine dato vince.
    env_vars = [model_env_var] if isinstance(model_env_var, str) else list(model_env_var or [])
    model = None
    for ev in env_vars:
        model = os.environ.get(ev, "").strip() or None
        if model:
            break
    if not model:
        model = fallback_model or defaults["chat_model"]

    kwargs = {"model": model, "temperature": temp, "api_key": api_key}
    if defaults["base_url"]:
        kwargs["base_url"] = defaults["base_url"]

    # ── OpenRouter-only: cheapest-provider routing + usage accounting ──────
    # Aggiunto SOLO sul branch openrouter (deepseek-direct/openai intatti).
    #   • provider.sort="price"  → Auto Min Price: instrada verso l'endpoint più
    #     economico, sovrascrivendo l'Auto Exacto (quality-first) che le richieste
    #     con tool-calling userebbero di default. Configurabile via
    #     OPENROUTER_PROVIDER_SORT (default "price"; "none"/vuoto → ometti il
    #     provider object, lasciando il routing di default di OpenRouter).
    #   • usage.include=true     → OpenRouter ritorna il costo REALE effettivamente
    #     fatturato + il dettaglio cache token nella usage della risposta, da cui
    #     il token_tracker estrae cost/cache_read/cache_write per-call.
    #   • provider.ignore=[…]    → esclude endpoint specifici (comma-separated in
    #     OPENROUTER_PROVIDER_IGNORE, es. "StreamLake,Baidu"): usato per scartare
    #     provider che ritornano content vuoto/reasoning-only o troncato. Con
    #     sort=price attivo, il routing sceglie il più economico TRA i rimanenti.
    #   • provider.only=[…]      → whitelist esclusiva (OPENROUTER_PROVIDER_ONLY);
    #     se data, il routing usa solo questi endpoint. Precede ignore.
    if provider == "openrouter":
        extra_body: dict = {"usage": {"include": True}}
        prov_obj: dict = {}
        sort = os.environ.get("OPENROUTER_PROVIDER_SORT", "price").strip().lower()
        if sort and sort != "none":
            prov_obj["sort"] = sort

        def _csv(env: str) -> list:
            return [p.strip() for p in os.environ.get(env, "").split(",") if p.strip()]

        only   = _csv("OPENROUTER_PROVIDER_ONLY")
        ignore = _csv("OPENROUTER_PROVIDER_IGNORE")
        if only:
            prov_obj["only"] = only
        if ignore:
            prov_obj["ignore"] = ignore
        if prov_obj:
            extra_body["provider"] = prov_obj
        kwargs["extra_body"] = extra_body

    # Token tracking: aggancia un callback taggato col nome dell'agente, così
    # ogni risposta LLM viene sommata all'accumulatore globale per-agente.
    # Un fallimento qui NON blocca il run, ma va DETTO: senza il callback i
    # contatori restano a zero e il report mostra costi nulli invece di quelli
    # reali — un dato sbagliato che sembra un dato valido.
    if agent:
        try:
            from core.token_tracker import TokenTrackingCallback
            if TokenTrackingCallback is None:
                raise RuntimeError("TokenTrackingCallback non disponibile "
                                   "(langchain_core.callbacks non importabile)")
            kwargs["callbacks"] = [TokenTrackingCallback(agent)]
        except Exception as e:
            import core.cli_output as _cli
            _cli.warn(f"[llm_factory] token tracking non attivo per '{agent}': {e} "
                      f"— i costi nel report saranno incompleti")

    # Branch openrouter → subclass che cattura il provider per-chiamata; gli altri
    # provider restano su ChatOpenAI puro (nessun campo provider da preservare).
    cls = _ProviderAwareChatOpenAI if provider == "openrouter" else ChatOpenAI
    return cls(**kwargs)


def get_current_provider() -> str:
    """Helper di diagnostica: mostra il provider in uso."""
    return _detect_provider()
