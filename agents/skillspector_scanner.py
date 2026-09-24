"""
SkillSpector Scanner
=====================
Wrapper attorno a NVIDIA SkillSpector (https://github.com/NVIDIA/skillspector,
Apache 2.0), vendorizzato in `vendor/skillspector/` — non un pacchetto pubblicato
su un registry stabile, quindi copiato nel repo invece di un `uvx pkg@latest`
come per Snyk (vedi vendor/skillspector/THIRD_PARTY_NOTICES.md per l'attribuzione).

Lanciato via `uv run --project vendor/skillspector` (build/venv locale al
progetto vendorizzato, cache dopo la prima chiamata — stessa ergonomia di uvx).

LLM analysis: riusa la OPENROUTER_API_KEY già configurata per Blue/Red, stesso
modello di default del resto della pipeline (deepseek/deepseek-v4-pro,
llm_factory.py). Anthropic è volutamente ESCLUSO dall'auto-detect: la sua API di
tool-use rifiuta lo schema JSON di SkillSpector (proprietà "minimum" su un
integer non supportata) — ogni analyzer semantico fallisce silenziosamente e lo
scan degrada a solo-statico senza dirlo. Meglio uno scan statico esplicito
(--no-llm) che uno "LLM" fasullo che non ha mai realmente girato.

Lo statico-only è ora SOLO una scelta esplicita (force_no_llm=True /
--skillspector-no-llm), per confrontare con/senza LLM a parità di skill. Senza
force_no_llm e senza credenziali compatibili la scan NON parte più in silenzio
su --no-llm: ritorna scan_error subito (nessun processo lanciato) — un
risultato "static-only" per mancanza di chiave sarebbe indistinguibile da uno
scelto apposta, e falserebbe il confronto.

Output:
{
  "findings":   list[dict],   # {"code", "severity", "title", "description"}
  "scan_error": str | None,
  "raw":        dict | str | None,
  "source":     "live",       # nessuna scorciatoia "cached" nota per SkillSpector
                               # (skills.sh non lo include tra i suoi 3 motori)
  "used_llm":   bool,         # True se l'analisi semantica ha girato, False se solo statica
}
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

VENDOR_DIR   = Path(__file__).resolve().parent.parent / "vendor" / "skillspector"
SCAN_TIMEOUT = 180
MAX_TIMEOUT_RETRIES = 2  # tentativi extra dopo il primo timeout (3 tentativi totali)
_RAW_TRUNCATE = 4000

_DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-pro"


def _model(default: str) -> str:
    """Modello per lo scan: override dedicato > modello della pipeline
    (SECURITY_MODEL, cioè quello scelto nel selector della WebUI) > default.

    Senza il gradino SECURITY_MODEL una run che seleziona un modello lo applicava
    solo a blue/red/tester, mentre questo scanner restava sul default hardcoded —
    silenziosamente, e con il report finale che dichiarava il modello scelto."""
    return (os.environ.get("SKILLSPECTOR_MODEL", "").strip()
            or os.environ.get("SECURITY_MODEL", "").strip()
            or default)


def _pick_provider_env() -> dict:
    """Sceglie provider/modello per l'analisi LLM di SkillSpector in base alle
    credenziali già disponibili nel progetto (stesso principio di
    main.py:_check_api_key). Preferenza: OpenRouter (stessa key/modello di
    default del resto della pipeline) > OpenAI diretto > nessuna LLM disponibile.
    Anthropic ESCLUSO di proposito (vedi docstring del modulo)."""
    if os.environ.get("OPENROUTER_API_KEY"):
        from agents import llm_proxy
        return {
            "SKILLSPECTOR_PROVIDER": "openai",
            "OPENAI_API_KEY":        os.environ["OPENROUTER_API_KEY"],
            # Passa dal proxy locale se attivo (token/costo reali, vedi
            # llm_proxy.py) — fallback diretto a OpenRouter se non lo è.
            "OPENAI_BASE_URL":       llm_proxy.base_url("skillspector") or "https://openrouter.ai/api/v1",
            "SKILLSPECTOR_MODEL":    _model(_DEFAULT_OPENROUTER_MODEL),
        }
    if os.environ.get("OPENAI_API_KEY"):
        env = {"SKILLSPECTOR_PROVIDER": "openai"}   # usa OPENAI_API_KEY/BASE_URL già in env
        # Modello esplicito solo se richiesto (override o modello della pipeline):
        # altrimenti si lascia il default di SkillSpector, che qui non conosciamo.
        model = _model("")
        if model:
            env["SKILLSPECTOR_MODEL"] = model
        return env
    return {}


def _capture_text(result: subprocess.CompletedProcess) -> str:
    """Concatena stderr+stdout (mai solo uno dei due): il CLI di skillspector usa
    `rich.Console` per il messaggio d'errore vero e proprio (va su stdout), mentre
    i DeprecationWarning di langchain/langgraph vanno su stderr — prendere solo
    stderr (perché non vuoto) nasconderebbe sempre l'errore reale dietro il rumore
    dei warning."""
    parts = [p.strip() for p in (result.stderr, result.stdout) if p and p.strip()]
    return "\n".join(parts)[:_RAW_TRUNCATE]


def _resolve_location_path(skill_path: str, rel_file: str) -> Optional[Path]:
    """Risolve location["file"] (relativo alla root scansionata da skillspector)
    contro il vero file sul disco. Rifiuta risoluzioni che escano dalla root
    (belt-and-suspenders — l'output è nostro/locale, non input untrusted, ma
    costa nulla)."""
    root = Path(skill_path)
    root = root if root.is_dir() else root.parent
    root = root.resolve()
    try:
        candidate = (root / rel_file).resolve()
        candidate.relative_to(root)
    except (ValueError, OSError):
        return None
    return candidate if candidate.is_file() else None


def _extract_snippet(skill_path: str, location: Optional[dict]) -> str:
    """Gli analyzer semantici puri (SDI/SQP/SSD — vedi commento sotto) non
    popolano mai code_snippet/finding, ma restituiscono SEMPRE un location.
    start_line/end_line genuino: il prompt LLM numera le righe del file
    (`number_lines()` in llm_analyzer_base.py) e chiede al modello di citarle,
    quindi il range è un riferimento reale al file, non un placeholder — lo
    risolviamo noi leggendo le righe corrispondenti dal file scansionato."""
    location = location or {}
    rel_file = location.get("file")
    start = location.get("start_line")
    if not rel_file or not isinstance(start, int) or start < 1:
        return ""
    path = _resolve_location_path(skill_path, rel_file)
    if not path:
        return ""
    end = location.get("end_line") or start
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    snippet = "\n".join(lines[start - 1:end])
    return snippet[:2000]


def _normalize_finding(raw: dict, skill_path: str) -> dict:
    # Forma reale (v2.2.3, --format json): {"id","category","pattern","severity",
    # "confidence","location","finding","explanation","remediation","code_snippet",
    # "intent"}. category/pattern/finding/code_snippet/intent sono spesso null per
    # i finding degli analyzer semantici (LLM) — solo id/severity/explanation
    # affidabili in ogni caso.
    title = raw.get("category") or raw.get("pattern") or raw.get("id") or ""
    desc  = raw.get("explanation") or raw.get("finding") or ""
    remediation = raw.get("remediation")
    if remediation:
        desc = f"{desc}\n\nRemediation: {remediation}" if desc else f"Remediation: {remediation}"
    quote = raw.get("code_snippet") or raw.get("finding") or ""
    if not quote:
        quote = _extract_snippet(skill_path, raw.get("location"))
    return {
        "code":        raw.get("id") or "",
        "severity":    (raw.get("severity") or "").lower(),
        "title":       title,
        "description": desc,
        "quote":       quote,
    }


def run(skill_path: str, force_no_llm: bool = False) -> dict:
    """Esegue `skillspector scan <skill_path> --format json` (via `uv run --project
    vendor/skillspector`) e normalizza l'output. Non solleva mai.

    force_no_llm=True forza lo scan solo-statico anche con credenziali LLM
    disponibili — per confrontare i risultati con/senza LLM a parità di skill
    (vedi run_skillspector/skillspector_no_llm in graph/nodes.py). Senza
    force_no_llm, credenziali mancanti sono un errore esplicito (scan_error),
    non un degrado silenzioso a statico."""
    if force_no_llm:
        provider_env, use_llm = {}, False
    else:
        provider_env = _pick_provider_env()
        if not provider_env:
            return {"findings": [], "scan_error":
                    "LLM richiesto ma nessuna credenziale compatibile trovata "
                    "(serve OPENROUTER_API_KEY o OPENAI_API_KEY) — usa "
                    "force_no_llm/--skillspector-no-llm per lo scan solo-statico esplicito.",
                    "raw": None, "source": "live", "used_llm": False}
        use_llm = True

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        out_path = Path(tf.name)

    try:
        cmd = ["uv", "run", "--project", str(VENDOR_DIR), "skillspector", "scan",
               skill_path, "--format", "json", "--output", str(out_path)]
        if not use_llm:
            cmd.append("--no-llm")

        env = {**os.environ, **provider_env}
        attempt = 0
        while True:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True,
                                         timeout=SCAN_TIMEOUT, env=env)
                break
            except FileNotFoundError:
                return {"findings": [], "scan_error": "uv non trovato — richiesto per skillspector.",
                        "raw": None, "source": "live", "used_llm": False}
            except subprocess.TimeoutExpired:
                if attempt >= MAX_TIMEOUT_RETRIES:
                    return {"findings": [], "scan_error":
                            f"skillspector timeout dopo {SCAN_TIMEOUT}s ({attempt + 1} tentativi)",
                            "raw": None, "source": "live", "used_llm": use_llm}
                attempt += 1
                out_path.unlink(missing_ok=True)  # scarta output parziale del tentativo scaduto

        # skillspector esce con codice 1 quando TROVA issue (convenzione stile
        # grep/CI-gate) — NON è un errore. Un errore vero è "nessun file di
        # output prodotto o illeggibile", non il returncode da solo. Si prova
        # sempre a leggere il file prima di arrendersi sul returncode.
        if not out_path.exists() or out_path.stat().st_size == 0:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"skillspector exit={result.returncode}: {err or 'nessun output prodotto'}",
                    "raw": None, "source": "live", "used_llm": use_llm}

        try:
            parsed = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as e:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"output non parsabile (exit={result.returncode}): {e} — {err}",
                    "raw": None, "source": "live", "used_llm": use_llm}

        issues   = parsed.get("issues") or []
        findings = [_normalize_finding(i, skill_path) for i in issues if isinstance(i, dict)]
        actually_used_llm = bool((parsed.get("metadata") or {}).get("llm_available"))
        return {"findings": findings, "scan_error": None, "raw": parsed,
                "source": "live", "used_llm": actually_used_llm}
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass
