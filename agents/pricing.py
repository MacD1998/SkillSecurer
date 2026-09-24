"""
agents/pricing.py — prezzi per-provider dall'endpoints API di OpenRouter
========================================================================
Un singolo modello su OpenRouter è servito da più endpoint (provider diversi,
quantizzazioni e prezzi diversi). L'endpoints API espone l'elenco con il prezzo
di ciascuno; lo usiamo per:
  • mostrare la tabella "API pricing" nel report (PROVIDER | QUANT | INPUT/M |
    OUTPUT/M | CACHE_READ/M | CACHE_WRITE/M), evidenziando il più economico;
  • arricchire il model selector del WebUI con i prezzi cache (oltre input/output).

OpenRouter espone i prezzi PER-TOKEN; qui i campi token-based vengono normalizzati
a $/M (per milione di token). request/image/internal_reasoning restano grezzi
(prezzo per-unità così com'è).

Tutto difensivo: chiave assente, fetch fallita o campi mancanti → [] / 0, mai
un'eccezione che blocchi la pipeline o il report.
"""
from __future__ import annotations

import json
import os
import urllib.request


def _per_million(v) -> float:
    """Prezzo per-token (string/float) → $/M. Difensivo: None/invalid → 0.0."""
    try:
        return round(float(v) * 1_000_000, 6)
    except (TypeError, ValueError):
        return 0.0


def _raw(v) -> float:
    """Prezzo per-unità così com'è (request/image/internal_reasoning). → 0.0 se invalid."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def get_endpoint_pricing(model_id: str, timeout: float = 15) -> list[dict]:
    """
    Prezzi per-endpoint di `model_id` (es. "deepseek/deepseek-v4-pro").

    Ritorna una lista di dict, uno per endpoint:
        {
          "provider_name":  str,
          "quantization":   str,
          "context_length": int,
          # token-based, normalizzati a $/M:
          "input":       float,   # pricing.prompt
          "output":      float,   # pricing.completion
          "cache_read":  float,   # pricing.input_cache_read
          "cache_write": float,   # pricing.input_cache_write
          # per-unità grezzi:
          "request":            float,
          "image":              float,
          "internal_reasoning": float,
        }
    [] se: model_id senza "/" (non è uno slug OpenRouter), chiave assente, fetch
    fallita o nessun endpoint. Non solleva mai eccezioni.
    """
    if not model_id or "/" not in model_id:
        return []
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return []

    author, _, slug = model_id.partition("/")
    author, slug = author.strip(), slug.strip()
    if not author or not slug:
        return []

    url = f"https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    body = data.get("data") or {}
    endpoints = body.get("endpoints") or []
    out: list[dict] = []
    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        pr = ep.get("pricing") or {}
        out.append({
            "provider_name":  ep.get("provider_name") or ep.get("name") or "—",
            "quantization":   ep.get("quantization") or "—",
            "context_length": _int(ep.get("context_length")),
            "input":          _per_million(pr.get("prompt")),
            "output":         _per_million(pr.get("completion")),
            "cache_read":     _per_million(pr.get("input_cache_read")),
            "cache_write":    _per_million(pr.get("input_cache_write")),
            "request":            _raw(pr.get("request")),
            "image":              _raw(pr.get("image")),
            "internal_reasoning": _raw(pr.get("internal_reasoning")),
        })
    return out
