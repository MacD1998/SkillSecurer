"""
AIG Skill Scanner
==================
Wrapper attorno a Tencent AI-Infra-Guard's aig-skill-scan
(https://github.com/Tencent/AI-Infra-Guard/tree/main/skill-scan, Apache 2.0),
pubblicato su PyPI come `aig-skill-scan` — lanciato via `uvx`, nessun vendoring
necessario (stesso principio di cisco_scanner.py).

Modalità default (NON --aig-mode): 1 sola stage (Code Audit), output SARIF
2.1.0 pulito su file. --aig-mode è volutamente ESCLUSO: è la pipeline a 3
stage (Info Collection → Code Audit → Vulnerability Review) pensata per il
frontend step-by-step della piattaforma AI-Infra-Guard, non per uso CLI
standalone — il loro stesso README lo sconsiglia ("no need to enable it
manually otherwise", "do not enable it when using pip install standalone":
inquina stdout di JSON di stato e scrive su file uno schema interno non
documentato). La modalità default costa 1 chiamata LLM per skill, stesso
ordine di grandezza di SkillSpector/Cisco.

LLM analysis: riusa la OPENROUTER_API_KEY già configurata per Blue/Red/
SkillSpector/Cisco, stesso modello di default del resto della pipeline
(deepseek/deepseek-v4-pro, llm_factory.py) — mappata su LLM_API_KEY/
LLM_BASE_URL/LLM_MODEL (schema proprietario dello scanner, accetta anche
OPENAI_* ma si usa il namespace dedicato per non toccare eventuali OPENAI_*
già in ambiente per altri scopi — stesso principio di
cisco_scanner.SKILL_SCANNER_LLM_*).

A differenza di SkillSpector/Cisco, aig-skill-scan NON ha un motore statico
sotto: è LLM-only, nessuna variante --no-llm esiste nel tool stesso. Senza
credenziali compatibili la scan NON parte: scan_error subito, nessun processo
lanciato — niente da "confrontare con/senza LLM" per questo motore.

Output:
{
  "findings":   list[dict],   # {"code", "severity", "title", "description", "quote"}
  "scan_error": str | None,
  "raw":        dict | str | None,
  "source":     "live",       # nessuna scorciatoia "cached" nota per aig-skill-scan
  "used_llm":   bool,         # sempre True su successo (motore LLM-only)
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
    return (os.environ.get("AIG_SCANNER_MODEL", "").strip()
            or os.environ.get("SECURITY_MODEL", "").strip()
            or default)


def _pick_llm_env() -> dict:
    """Sceglie le env var LLM per aig-skill-scan in base alle credenziali già
    disponibili nel progetto (stesso principio di
    cisco_scanner._pick_llm_env/skillspector_scanner._pick_provider_env)."""
    if os.environ.get("OPENROUTER_API_KEY"):
        from agents import llm_proxy
        return {
            "LLM_API_KEY":  os.environ["OPENROUTER_API_KEY"],
            # Passa dal proxy locale se attivo (token/costo reali, vedi
            # llm_proxy.py) — fallback diretto a OpenRouter se non lo è.
            "LLM_BASE_URL": llm_proxy.base_url("aig") or "https://openrouter.ai/api/v1",
            "LLM_MODEL":    _model(_DEFAULT_OPENROUTER_MODEL),
        }
    if os.environ.get("OPENAI_API_KEY"):
        return {
            "LLM_API_KEY": os.environ["OPENAI_API_KEY"],
            "LLM_MODEL":   _model("gpt-4o-mini"),
        }
    return {}


def _capture_text(result: subprocess.CompletedProcess) -> str:
    parts = [p.strip() for p in (result.stderr, result.stdout) if p and p.strip()]
    return "\n".join(parts)[:_RAW_TRUNCATE]


def _resolve_target(root: Path) -> tuple[str, Optional[Path]]:
    """aig-skill-scan vuole una DIRECTORY (--repo), non richiede un filename
    letterale come Cisco (nessun requisito "SKILL.md"). Ma va comunque isolato
    un file per volta: passare il parent di un'injection scansionerebbe tutte
    le injection della stessa cartella insieme, con la stessa attribuzione
    rotta descritta in cisco_scanner._resolve_target.

    Ritorna (target_dir, staged_dir_da_rimuovere_o_None)."""
    if root.is_dir():
        return str(root), None
    staged = Path(tempfile.mkdtemp(prefix="aig_scan_"))
    shutil.copy2(root, staged / root.name)
    return str(staged), staged


def _resolve_location_path(target_dir: str, uri: str) -> Optional[Path]:
    """Risolve locations[].physicalLocation.artifactLocation.uri (relativo alla
    root scansionata) contro il vero file sul disco, rifiutando risoluzioni che
    escano dalla root (l'output è nostro/locale, non input untrusted, ma costa
    nulla — stesso principio di skillspector_scanner._resolve_location_path)."""
    root = Path(target_dir).resolve()
    try:
        candidate = (root / uri).resolve()
        candidate.relative_to(root)
    except (ValueError, OSError):
        return None
    return candidate if candidate.is_file() else None


def _extract_snippet(target_dir: str, result: dict) -> str:
    locations = result.get("locations") or []
    if not locations or not isinstance(locations[0], dict):
        return ""
    phys = locations[0].get("physicalLocation") or {}
    uri = ((phys.get("artifactLocation") or {}).get("uri") or "").strip()
    region = phys.get("region") or {}
    start = region.get("startLine")
    if not uri or not isinstance(start, int) or start < 1:
        return ""
    path = _resolve_location_path(target_dir, uri)
    if not path:
        return ""
    end = region.get("endLine") or start
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[start - 1:end])[:2000]


def _normalize_finding(result: dict, target_dir: str) -> dict:
    # Forma SARIF 2.1.0 (unico formato prodotto in modalità default — vedi
    # docstring del modulo): {"ruleId","level","message":{"text"},"locations":
    # [...],"fixes":[{"description":{"text"}}, ...]}. ruleId è la tassonomia
    # SkillTrustBench T01-T09.
    desc = ((result.get("message") or {}).get("text") or "")
    remediations = [f.get("description", {}).get("text") for f in (result.get("fixes") or [])
                    if isinstance(f, dict) and (f.get("description") or {}).get("text")]
    if remediations:
        rem = "\n".join(remediations)
        desc = f"{desc}\n\nRemediation: {rem}" if desc else f"Remediation: {rem}"
    return {
        "code":        result.get("ruleId") or "",
        "severity":    (result.get("level") or "").lower(),
        "title":       result.get("ruleId") or "",
        "description": desc,
        "quote":       _extract_snippet(target_dir, result),
    }


def run(skill_path: str) -> dict:
    """Esegue `aig-skill-scan --repo <dir> --language en -o <file>` (via uvx,
    modalità default, non --aig-mode — vedi docstring del modulo) e normalizza
    l'output SARIF. Non solleva mai: errori/timeout finiscono in scan_error,
    findings=[].

    Motore LLM-only: senza credenziali compatibili la scan non parte affatto
    (scan_error immediato, nessun processo lanciato) — nessuna variante
    solo-statica esiste per questo tool (a differenza di
    skillspector_scanner.py/cisco_scanner.py)."""
    llm_env = _pick_llm_env()
    if not llm_env:
        return {"findings": [], "scan_error":
                "LLM richiesto ma nessuna credenziale compatibile trovata "
                "(serve OPENROUTER_API_KEY o OPENAI_API_KEY) — aig-skill-scan "
                "non ha una modalità solo-statica.",
                "raw": None, "source": "live", "used_llm": False}

    root = Path(skill_path)
    try:
        target, staged = _resolve_target(root)
    except OSError as e:
        return {"findings": [], "scan_error": f"impossibile preparare la skill-dir per lo scan: {e}",
                "raw": None, "source": "live", "used_llm": False}

    with tempfile.NamedTemporaryFile(suffix=".sarif.json", delete=False) as tf:
        out_path = Path(tf.name)

    # --base_url/-m ESPLICITI, non solo LLM_BASE_URL/LLM_MODEL in env: nel CLI
    # (v0.2.1, skill_scan/main.py resolve_runtime_override) `args.base_url` e
    # `args.model` hanno un default argparse NON vuoto (config.DEFAULT_BASE_URL/
    # DEFAULT_MODEL), quindi `args.base_url or os.getenv("LLM_BASE_URL")` non
    # legge MAI la env var — resta sempre https://openrouter.ai/api/v1 diretto,
    # bypassando in silenzio il proxy locale (vedi agents/llm_proxy.py) e il
    # modello richiesto. Solo LLM_API_KEY funziona da env (args.api_key default
    # None). I flag CLI non hanno questo bug — bypassano args.base_url/model.
    cmd = ["uvx", "--from", "aig-skill-scan", "aig-skill-scan", "--repo", target,
           "--language", "en", "-o", str(out_path)]
    if llm_env.get("LLM_BASE_URL"):
        cmd += ["--base_url", llm_env["LLM_BASE_URL"]]
    if llm_env.get("LLM_MODEL"):
        cmd += ["-m", llm_env["LLM_MODEL"]]
    env = {**os.environ, **llm_env}

    try:
        attempt = 0
        while True:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True,
                                         timeout=SCAN_TIMEOUT, env=env)
                break
            except FileNotFoundError:
                return {"findings": [], "scan_error": "uvx non trovato — richiesto per aig-skill-scan.",
                        "raw": None, "source": "live", "used_llm": False}
            except subprocess.TimeoutExpired:
                if attempt >= MAX_TIMEOUT_RETRIES:
                    return {"findings": [], "scan_error":
                            f"aig-skill-scan timeout dopo {SCAN_TIMEOUT}s ({attempt + 1} tentativi)",
                            "raw": None, "source": "live", "used_llm": True}
                attempt += 1
                out_path.unlink(missing_ok=True)  # scarta output parziale del tentativo scaduto

        if not out_path.exists() or out_path.stat().st_size == 0:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"aig-skill-scan exit={result.returncode}: {err or 'nessun output prodotto'}",
                    "raw": None, "source": "live", "used_llm": True}

        try:
            parsed = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as e:
            err = _capture_text(result)
            return {"findings": [], "scan_error": f"output non parsabile (exit={result.returncode}): {e} — {err}",
                    "raw": None, "source": "live", "used_llm": True}

        runs = parsed.get("runs") or []
        results = (runs[0].get("results") or []) if runs and isinstance(runs[0], dict) else []
        findings = [_normalize_finding(r, target) for r in results if isinstance(r, dict)]
        return {"findings": findings, "scan_error": None, "raw": parsed,
                "source": "live", "used_llm": True}
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)
