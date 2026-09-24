"""
Cisco Skill Scanner
====================
Wrapper attorno a Cisco AI Defense's skill-scanner
(https://github.com/cisco-ai-defense/skill-scanner, Apache 2.0), pubblicato su
PyPI come `cisco-ai-skill-scanner` — lanciato via `uvx`, nessun vendoring
necessario (a differenza di SkillSpector, vedi agents/skillspector_scanner.py:
NVIDIA non pubblica un pacchetto stabile su un registry, Cisco sì).

LLM analysis: riusa la OPENROUTER_API_KEY già configurata per Blue/Red/
SkillSpector, stesso modello di default del resto della pipeline
(deepseek/deepseek-v4-pro, llm_factory.py) — ma mappata sulle env var
proprietarie dello scanner (SKILL_SCANNER_LLM_* — schema OpenAI-compatible
custom-endpoint diverso da OPENAI_*/ANTHROPIC_*, vedi loro .env.example).

Lo statico-only è ora SOLO una scelta esplicita (force_no_llm=True /
--cisco-no-llm), per confrontare con/senza LLM a parità di skill — stesso
principio di skillspector_scanner.py. Senza force_no_llm e senza credenziali
compatibili la scan NON parte più in silenzio su solo-statico: ritorna
scan_error subito (nessun processo lanciato).

Output:
{
  "findings":   list[dict],   # {"code", "severity", "title", "description", "quote"}
  "scan_error": str | None,
  "raw":        dict | str | None,
  "source":     "live",       # nessuna scorciatoia "cached" nota per Cisco skill-scanner
  "used_llm":   bool,         # True se --use-llm è girato (credenziali disponibili)
}
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

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
    return (os.environ.get("CISCO_SCANNER_MODEL", "").strip()
            or os.environ.get("SECURITY_MODEL", "").strip()
            or default)


def _pick_llm_env() -> dict:
    """Sceglie le env var LLM per skill-scanner in base alle credenziali già
    disponibili nel progetto (stesso principio di
    skillspector_scanner._pick_provider_env). skill-scanner usa un proprio
    schema SKILL_SCANNER_LLM_* — non OPENAI_API_KEY/OPENAI_BASE_URL
    direttamente — quindi la mappatura è esplicita invece di un semplice
    pass-through env."""
    if os.environ.get("OPENROUTER_API_KEY"):
        from agents import llm_proxy
        return {
            "SKILL_SCANNER_LLM_API_KEY":  os.environ["OPENROUTER_API_KEY"],
            "SKILL_SCANNER_LLM_PROVIDER": "openai",
            # Passa dal proxy locale se attivo (token/costo reali, vedi
            # llm_proxy.py) — fallback diretto a OpenRouter se non lo è.
            "SKILL_SCANNER_LLM_BASE_URL": llm_proxy.base_url("cisco") or "https://openrouter.ai/api/v1",
            "SKILL_SCANNER_LLM_MODEL":    _model(_DEFAULT_OPENROUTER_MODEL),
        }
    if os.environ.get("OPENAI_API_KEY"):
        return {
            "SKILL_SCANNER_LLM_API_KEY": os.environ["OPENAI_API_KEY"],
            "SKILL_SCANNER_LLM_MODEL":   _model("gpt-4o-mini"),
        }
    return {}


def _capture_text(result: subprocess.CompletedProcess) -> str:
    parts = [p.strip() for p in (result.stderr, result.stdout) if p and p.strip()]
    return "\n".join(parts)[:_RAW_TRUNCATE]


def _normalize_finding(raw: dict) -> dict:
    # Forma reale osservata (v0.x, --format json): {"id","rule_id","category",
    # "severity","title","description","file_path","line_number","snippet",
    # "remediation","analyzer","metadata"}. snippet è la quota più vicina a un
    # ancoraggio testuale — spesso null per finding LLM-only (nessuna riga
    # precisa, solo un verdetto semantico sul file/description).
    return {
        "code":        raw.get("rule_id") or raw.get("id") or "",
        "severity":    (raw.get("severity") or "").lower(),
        "title":       raw.get("title") or "",
        "description": raw.get("description") or "",
        "quote":       raw.get("snippet") or "",
    }


def _resolve_target(root: Path) -> tuple[str, Optional[Path]]:
    """skill-scanner e' un loader di *directory-skill*: carica la cartella e vi
    cerca un file chiamato letteralmente SKILL.md ("Error loading skill: SKILL.md
    not found in <dir>"). Non basta quindi passare il parent di un .md qualsiasi,
    a differenza di snyk/skillspector che accettano il path del file.

    Due casi distinti:
      - file gia' chiamato SKILL.md -> si scansiona il parent, che e' una
        skill-dir vera (es. skills_sh_dataset): i file companion (script, ecc.)
        entrano nello scan, ed e' quello che vogliamo.
      - qualunque altro nome (es. l'output di Red, `<skill>__<vuln>__K3.md`,
        9 injection diverse nella stessa cartella) -> si stagia SOLO quel file in
        una temp dir come SKILL.md. Passare il parent scansionerebbe tutte le
        injection insieme e `_parallel_scanner_node` assegnerebbe gli stessi
        finding a tutti i record: attribuzione per-injection distrutta, senza
        alcun errore visibile.

    Ritorna (target_dir, staged_dir_da_rimuovere_o_None)."""
    if root.is_dir():
        return str(root), None
    if root.name == "SKILL.md":
        return str(root.parent), None
    staged = Path(tempfile.mkdtemp(prefix="cisco_scan_"))
    shutil.copy2(root, staged / "SKILL.md")
    return str(staged), staged


def run(skill_path: str, force_no_llm: bool = False) -> dict:
    """Esegue `skill-scanner scan <dir> --format json --output-json <file>`
    (via uvx) sulla skill-dir che contiene skill_path, e normalizza l'output.
    Non solleva mai: errori/timeout finiscono in scan_error, findings=[].

    force_no_llm=True forza lo scan solo-statico anche con credenziali LLM
    disponibili — per confrontare i risultati con/senza LLM a parità di skill
    (vedi run_cisco/cisco_no_llm in graph/nodes.py). Senza force_no_llm,
    credenziali mancanti sono un errore esplicito (scan_error), non un degrado
    silenzioso a statico."""
    if force_no_llm:
        llm_env = {}
    else:
        llm_env = _pick_llm_env()
        if not llm_env:
            return {"findings": [], "scan_error":
                    "LLM richiesto ma nessuna credenziale compatibile trovata "
                    "(serve OPENROUTER_API_KEY o OPENAI_API_KEY) — usa "
                    "force_no_llm/--cisco-no-llm per lo scan solo-statico esplicito.",
                    "raw": None, "source": "live", "used_llm": False}
    used_llm = bool(llm_env)

    root = Path(skill_path)
    try:
        target, staged = _resolve_target(root)
    except OSError as e:
        return {"findings": [], "scan_error": f"impossibile preparare la skill-dir per lo scan: {e}",
                "raw": None, "source": "live", "used_llm": used_llm}

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        out_path = Path(tf.name)

    cmd = ["uvx", "--from", "cisco-ai-skill-scanner", "skill-scanner", "scan",
           target, "--format", "json", "--output-json", str(out_path)]
    if used_llm:
        cmd += ["--use-llm", "--enable-meta"]

    env = {**os.environ, **llm_env}
    try:
        attempt = 0
        while True:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True,
                                         timeout=SCAN_TIMEOUT, env=env)
                break
            except FileNotFoundError:
                return {"findings": [], "scan_error": "uvx non trovato — richiesto per skill-scanner.",
                        "raw": None, "source": "live", "used_llm": False}
            except subprocess.TimeoutExpired:
                if attempt >= MAX_TIMEOUT_RETRIES:
                    return {"findings": [], "scan_error":
                            f"skill-scanner timeout dopo {SCAN_TIMEOUT}s ({attempt + 1} tentativi)",
                            "raw": None, "source": "live", "used_llm": used_llm}
                attempt += 1
                out_path.unlink(missing_ok=True)  # scarta output parziale del tentativo scaduto

        # skill-scanner puo' uscire non-zero anche solo per aver TROVATO
        # findings (--fail-on-findings/--fail-on-severity, qui non passati, ma
        # meglio non fidarsi del solo returncode) — un errore vero è "nessun
        # file di output prodotto o illeggibile".
        if not out_path.exists() or out_path.stat().st_size == 0:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"skill-scanner exit={result.returncode}: {err or 'nessun output prodotto'}",
                    "raw": None, "source": "live", "used_llm": used_llm}

        try:
            parsed = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as e:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"output non parsabile (exit={result.returncode}): {e} — {err}",
                    "raw": None, "source": "live", "used_llm": used_llm}

        findings = [_normalize_finding(f) for f in (parsed.get("findings") or [])
                    if isinstance(f, dict) and (f.get("severity") or "").lower() != "info"]
        return {"findings": findings, "scan_error": None, "raw": parsed,
                "source": "live", "used_llm": used_llm}
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)
