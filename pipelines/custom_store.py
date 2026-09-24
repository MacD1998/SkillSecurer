"""
Persistenza dei preset di pipeline custom (CRUD su file JSON).
==============================================================
Un file JSON per preset sotto `pipelines/custom/<slug>.json` (preferito al file
indice unico: i preset restano facili da versionare/condividere/diff-are, come da
specifica). Nessun database — coerente con lo stack del progetto.

API:
  list_custom_pipelines()      -> list[dict]   (metadati, ordinati per updated_at)
  save_custom_pipeline(cfg)    -> dict         (valida, scrive, ritorna i metadati)
  load_custom_pipeline(name)   -> PipelineConfig
  delete_custom_pipeline(name) -> bool
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from pipelines.custom_config import PipelineConfig, validate_or_raise

# Directory dedicata, separata dallo storico delle run (results/).
CUSTOM_DIR = Path(__file__).resolve().parent / "custom"


def _slug(name: str) -> str:
    """Nome file deterministico e sicuro a partire dal nome del preset."""
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", (name or "").strip().lower()).strip("-")
    return s or "preset"


def _path_for(name: str) -> Path:
    return CUSTOM_DIR / f"{_slug(name)}.json"


def _ensure_dir() -> None:
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)


def _meta(cfg: PipelineConfig) -> dict:
    """Riassunto leggero per il selettore della WebUI (badge 'custom', edit, ecc.)."""
    return {
        "name":        cfg.name,
        "slug":        _slug(cfg.name),
        "source_type": cfg.source.type,
        # "blue" resta nel meta (il selettore della WebUI lo legge come booleano);
        # "defense" porta la selezione completa dei motori.
        "blue":        cfg.defense.has_blue,
        "defense":     list(cfg.defense.engines),
        "eval":        cfg.eval_enabled,
        "tester":      cfg.tester.enabled,
        "tester_scope": cfg.tester.scope,
        "created_at":  cfg.created_at,
        "updated_at":  cfg.updated_at,
        "custom":      True,
    }


def list_custom_pipelines() -> List[dict]:
    """Metadati di tutti i preset salvati (più recente prima). File illeggibili saltati."""
    if not CUSTOM_DIR.is_dir():
        return []
    out: List[dict] = []
    for jf in CUSTOM_DIR.glob("*.json"):
        try:
            cfg = PipelineConfig.from_dict(json.loads(jf.read_text(encoding="utf-8")))
        except Exception:
            continue
        out.append(_meta(cfg))
    out.sort(key=lambda m: m.get("updated_at") or "", reverse=True)
    return out


def save_custom_pipeline(cfg: PipelineConfig) -> dict:
    """Valida (matrice) e scrive il preset. Imposta created_at/updated_at.
    Sovrascrive un preset con lo stesso slug (edit/duplicate con nome uguale)."""
    creating = not _path_for(cfg.name).exists()
    validate_or_raise(cfg)
    cfg.touch(creating=creating)
    _ensure_dir()
    _path_for(cfg.name).write_text(
        json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return _meta(cfg)


def load_custom_pipeline(name: str) -> PipelineConfig:
    """Carica un preset per nome (o slug). Alza FileNotFoundError se assente."""
    p = _path_for(name)
    if not p.exists():
        raise FileNotFoundError(f"Preset custom non trovato: {name}")
    return PipelineConfig.from_dict(json.loads(p.read_text(encoding="utf-8")))


def delete_custom_pipeline(name: str) -> bool:
    """Elimina un preset. Ritorna True se esisteva."""
    p = _path_for(name)
    if p.exists():
        p.unlink()
        return True
    return False


def find_path(name: str) -> Optional[Path]:
    p = _path_for(name)
    return p if p.exists() else None
