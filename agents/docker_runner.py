"""
Docker Runner
=============
Container persistente — aperto una volta, riusato per tutta la sessione.

Invece di creare/distruggere un container per ogni tentativo del tester
(240 cold start per un run completo), manteniamo un container attivo e
gli inviamo i comandi via `docker exec`.

Il SKILL.md viene aggiornato nel container tramite `docker cp` prima
di ogni nuova injection — molto più veloce di un cold start.

Ciclo di vita del container:
  start_container()  → avvia il container (una volta per benchmark)
  set_skill()        → copia il SKILL.md nel container (per ogni injection)
  exec_agent()       → esegue run_agent.py con il prompt
  stop_container()   → ferma e rimuove il container (fine benchmark)
"""
import hashlib
import json
import os
import shlex
import subprocess
import threading
import time
from pathlib import Path

import core.cli_output as cli


# Directory delle skill dentro il container target. Deve combaciare con la
# `base` di docker/run_agent.py:load_skill.
_SKILLS_ROOT = "/root/.claude/skills"

# Docker network of the target containers.
_POOL_NETWORK = "bridge"


# Variabili che contengono un SEGRETO. Vengono passate a `docker run` in forma
# "bare" (--env NOME, senza =valore): docker legge il valore dal proprio ambiente,
# che eredita da questo processo, e la chiave non compare mai in argv. Con la
# forma --env NOME=valore l'intera API key finiva nella riga di comando, quindi
# era leggibile da QUALUNQUE utente locale con un semplice `ps aux`.
# (Il valore resta visibile in `docker inspect`, come per ogni variabile passata a
# un container: quello richiede però accesso al socket docker, che sull'host è già
# equivalente a root — non è una superficie che si possa ridurre da qui.)
_SECRET_ENV = ("OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY")

# Variabili di configurazione NON segrete: passate con valore esplicito, così il
# default host-side resta l'unica sorgente di verità anche quando la var non è
# impostata nell'ambiente.
_CONFIG_ENV = (
    ("LLM_PROVIDER",    ""),
    ("SECURITY_MODEL",  ""),
    ("MAX_ITERATIONS",  "15"),
    ("API_TIMEOUT",     "90"),
    ("API_MAX_RETRIES", "5"),
    # Routing OpenRouter (stesso schema di llm_factory/llm_proxy): permette al
    # target agent di riportare cost/provider REALI (usage.include, vedi
    # docker/run_agent.py:_openrouter_extra) con lo stesso routing cheapest-
    # provider/esclusioni del resto della pipeline, invece del default quality-
    # first di OpenRouter usato in silenzio finora.
    ("OPENROUTER_PROVIDER_SORT",   "price"),
    ("OPENROUTER_PROVIDER_ONLY",   ""),
    ("OPENROUTER_PROVIDER_IGNORE", ""),
)


def _env_args() -> list[str]:
    """Argomenti --env per `docker run`: segreti in forma bare, config con valore."""
    args: list[str] = []
    for name in _SECRET_ENV:
        # Solo se davvero presente: un --env bare su una var non impostata è un
        # no-op per docker, ma ometterlo rende esplicito cosa viene propagato.
        if os.environ.get(name):
            args += ["--env", name]
    for name, default in _CONFIG_ENV:
        value = os.environ.get(name, default)
        if name == "SECURITY_MODEL":
            # Override per il target agent: docker/run_agent.py dentro il
            # container legge SOLO SECURITY_MODEL (non ha un client langchain
            # multi-env-var come llm_factory), quindi la risoluzione
            # TARGET_MODEL → SECURITY_MODEL va fatta qui, host-side.
            value = os.environ.get("TARGET_MODEL", "").strip() or value
        args += ["--env", f"{name}={value}"]
    return args


# ── Preflight ─────────────────────────────────────────────────────────

def preflight(docker_image: str = "sse3-target") -> list[str]:
    """Verifica che il tester possa davvero girare. Ritorna la lista dei problemi
    bloccanti — vuota se è tutto a posto.

    Va chiamata PRIMA di far partire la pipeline, non quando serve il container.
    Il primo contatto con Docker avviene in node_tester_judge, cioè DOPO che Red
    e Blue hanno già chiamato l'LLM: su un run da 391 injection sono ~7 USD spesi
    per poi fermarsi su un demone spento. Qui costa tre comandi e un secondo.

    Tre controlli distinti, perché richiedono tre rimedi diversi:
      1. la CLI `docker` esiste nel PATH        → Docker non installato
      2. il demone risponde                     → Docker installato ma fermo
      3. l'immagine target esiste               → va costruita
    """
    problems: list[str] = []

    try:
        subprocess.run(["docker", "version", "--format", "{{.Client.Version}}"],
                       capture_output=True, timeout=10, check=True)
    except FileNotFoundError:
        return ["comando `docker` non trovato nel PATH — Docker non è installato "
                "(o, sotto WSL, l'integrazione con Docker Desktop è disattivata)"]
    except subprocess.TimeoutExpired:
        return ["`docker version` non risponde entro 10s — demone in avvio o bloccato"]
    except subprocess.CalledProcessError as e:
        return [f"`docker version` fallisce: {(e.stderr or b'').decode(errors='ignore').strip()[:200]}"]

    # Il client risponde anche a demone spento: serve un comando che lo interroghi.
    try:
        r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            problems.append("demone Docker non raggiungibile — avvia Docker Desktop "
                            "(o `sudo systemctl start docker`)")
    except subprocess.TimeoutExpired:
        problems.append("il demone Docker non risponde entro 15s (in avvio?)")

    # Immagine target: senza, ogni `docker run` fallirebbe injection per injection.
    if not problems:
        r = subprocess.run(["docker", "image", "inspect", docker_image],
                           capture_output=True, timeout=15)
        if r.returncode != 0:
            problems.append(f"immagine '{docker_image}' assente — costruiscila con: "
                            f"docker build -t {docker_image} docker/")

    return problems


# ── Container persistente ─────────────────────────────────────────────

_container_id:   str | None = None
_container_name: str        = "sse3-agent"
_docker_image:   str        = "sse3-target"

# Timeout per docker exec — DEVE essere > MAX_ITERATIONS × API_TIMEOUT per evitare
# che docker exec tagli prima che il budget di iterazioni sia esaurito.
# Con MAX_ITERATIONS=15 e API_TIMEOUT=90s il caso peggiore è 1350s: 1800 mantiene
# margine, così una run lenta non viene uccisa come [TIMEOUT] prima di raggiungere
# i 15 turni ([MAX_ITERATIONS]). NB: se alzi MAX_ITERATIONS o API_TIMEOUT, rialza
# anche questi valori di conseguenza.
_TIMEOUT_BY_VULN = {
    "resource_exhaustion": 1860,  # backstop per loop infiniti (1800 + margine)
}
_DEFAULT_TIMEOUT = 1800  # margine su MAX_ITERATIONS(15) × API_TIMEOUT(90s) = 1350s


def start_container(docker_image: str = "sse3-target") -> None:
    """
    Avvia il container persistente in background.
    Il container rimane in esecuzione con `sleep infinity` come entrypoint.
    Il SKILL.md viene copiato via docker cp prima di ogni test.
    """
    global _container_id, _container_name, _docker_image
    _docker_image = docker_image

    # Ferma eventuale container precedente
    stop_container()

    cmd = [
        "docker", "run",
        "--rm",                    # auto-remove quando fermato
        "--detach",                # background
        "--name", _container_name,
        "--add-host", "host.docker.internal:host-gateway",
        # API key + config del provider (segreti in forma bare, vedi _env_args)
        *_env_args(),
        "--memory", "4g",
        "--cpus",   "1",
        "--network", _POOL_NETWORK,
        docker_image,
        "sleep", "infinity",       # mantiene il container attivo
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"docker run failed: {result.stderr}")
        _container_id = result.stdout.strip()
        cli.debug(f"   🐳 Container avviato: {_container_name} ({_container_id[:12]})")
    except FileNotFoundError:
        raise RuntimeError("Docker non trovato.")
    except Exception as e:
        raise RuntimeError(f"Impossibile avviare il container: {e}")


def stop_container() -> None:
    """Ferma e rimuove il container persistente."""
    global _container_id
    try:
        # Verifica se il container esiste prima di fermarlo
        check = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", _container_name],
            capture_output=True, text=True, timeout=5
        )
        if check.returncode != 0:
            # Container non esiste — nulla da fermare
            _container_id = None
            return
        subprocess.run(
            ["docker", "stop", _container_name],
            capture_output=True, timeout=15
        )
        _container_id = None
        cli.debug(f"   🐳 Container fermato: {_container_name}")
    except Exception as e:
        cli.warn(f"[DockerRunner] stop_container failed for {_container_name}: {e}")
        _container_id = None


# ── Container pool (esecuzione parallela) ─────────────────────────────
#
# Per parallelizzare i prompt di una versione usiamo N container distinti
# (sse3-agent-0 .. sse3-agent-(N-1)), ognuno con il proprio SKILL.md — nessuno
# stato condiviso lato container.

_pool: list[str] = []


def _pool_run_args(name: str, docker_image: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--detach", "--name", name,
        "--add-host", "host.docker.internal:host-gateway",
        # API key + config del provider (segreti in forma bare, vedi _env_args)
        *_env_args(),
        "--memory", "4g",
        "--cpus",   "2",
        "--network", _POOL_NETWORK,
        docker_image,
        "sleep", "infinity",
    ]


def start_container_pool(n: int, docker_image: str = "sse3-target") -> list[str]:
    """
    Avvia un pool di n container (sse3-agent-0 .. sse3-agent-(n-1)), ognuno con
    `sleep infinity`. Ritorna la lista dei nomi. Pulisce eventuali container
    omonimi rimasti da run precedenti prima di crearli.
    """
    global _pool, _docker_image
    _docker_image = docker_image
    stop_container_pool()

    names: list[str] = []
    for idx in range(n):
        name = f"sse3-agent-{idx}"
        # Rimuove eventuale container omonimo orfano (run precedente non pulita)
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)
        result = subprocess.run(_pool_run_args(name, docker_image),
                                capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            # Rollback: ferma quelli già avviati per non lasciare orfani
            for started in names:
                subprocess.run(["docker", "stop", started], capture_output=True, timeout=15)
            _pool = []
            raise RuntimeError(f"docker run failed per {name}: {result.stderr}")
        cli.debug(f"   🐳 Pool container avviato: {name} ({result.stdout.strip()[:12]})")
        names.append(name)

    _pool = names
    cli.debug(f"   🐳 Pool pronto: {n} container")
    return names


def stop_container_pool() -> None:
    """Ferma e rimuove tutti i container del pool."""
    global _pool
    for name in list(_pool):
        try:
            subprocess.run(["docker", "stop", name], capture_output=True, timeout=15)
        except Exception as e:
            cli.warn(f"[DockerRunner] stop_container_pool failed for {name}: {e}")
    if _pool:
        cli.debug(f"   🐳 Pool fermato: {len(_pool)} container")
    _pool = []


# ── Workspace lifecycle (EnvironmentAgent) ────────────────────────────

def reset_workspace(container_name: str = "sse3-agent") -> None:
    """
    Riporta /workspace allo snapshot git corrente (HEAD = ambiente preparato
    dall'EnvironmentAgent, o il commit iniziale del Dockerfile se nessun env è
    stato preparato). Rimuove i file creati dall'agente nel tentativo precedente.
    Non solleva mai (il `; true` finale garantisce rc 0).

    NB: `git clean -ffdx` (doppia -f) rimuove anche i repo git ANNIDATI creati
    dall'agente durante il tentativo (es. /workspace/repo/.git). Con una sola -f
    `git clean` salta le directory che contengono un .git, lasciandole tra un
    attempt e l'altro → contaminazione. La doppia -f le elimina.
    """
    try:
        subprocess.run(
            ["docker", "exec", container_name, "bash", "-c",
             "cd /workspace && git checkout -- . && git clean -ffdx 2>/dev/null; true"],
            capture_output=True, timeout=30,
        )
    except Exception as e:
        cli.warn(f"[DockerRunner] reset_workspace failed for {container_name}: {e}")


def set_skill(skill_path: str, container_name: str = "sse3-agent") -> tuple[str, str]:
    """
    Copia il SKILL.md nello specifico container via docker cp.
    Molto più veloce di un cold start — <1s. Nessuno stato condiviso tra
    container: ognuno ha la propria copia in /root/.claude/skills/.

    La skills dir del container viene SVUOTATA prima di ogni copia, così vi
    resta ESATTAMENTE una skill. Senza il wipe le skill delle injection
    precedenti si accumulavano e il match per nome lato container (run_agent.
    load_skill) poteva risolvere sulla skill sbagliata — l'attempt veniva
    eseguito su un altro SKILL.md, falsando ASR e funzionalità in silenzio.

    Returns:
        (skill_name, host_kb_line)
        skill_name:    derivato dal filename (oppure dalla parent dir se il
                       file è il canonico SKILL.md della versione BASE).
        host_kb_line:  riga "[KnowledgeBase] Loaded: ..." sintetizzata
                       host-side, usata da run_target come fallback quando
                       il container viene killato prima di poter loggare la
                       propria — situazione tipica in caso di TIMEOUT,
                       cioè proprio quando vorresti più info di audit.
    """
    skill_path = Path(skill_path).resolve()
    stem = skill_path.stem.split("__")[0]
    # Caso BASE: file 'SKILL.md' → stem 'SKILL' → ricade sul nome della parent dir.
    # Caso INJECTED/FIXED: file 'git__vuln__K3.md' → stem 'git__...' → split → 'git'.
    skill_name = skill_path.parent.name if stem.upper() == "SKILL" else stem
    dest_dir   = f"{_SKILLS_ROOT}/{skill_name}"

    # md5 host-side (combacia con quello loggato dal container — stesso file)
    content = skill_path.read_bytes()
    md5 = hashlib.md5(content).hexdigest()[:8]
    host_kb = (f"[KnowledgeBase] Loaded: {dest_dir}/SKILL.md "
               f"({len(content)} chars, md5={md5}) [host-side]")

    # Wipe + mkdir in un solo exec: la skills dir resta con la SOLA skill di
    # questo attempt. shlex.quote perché skill_name deriva da un nome di file
    # dell'utente (pipeline blue-only/custom) e finisce dentro `bash -c`.
    q_dest = shlex.quote(dest_dir)
    subprocess.run(
        ["docker", "exec", container_name, "bash", "-c",
         f"rm -rf {_SKILLS_ROOT}/* && mkdir -p {q_dest}"],
        capture_output=True, timeout=15
    )
    subprocess.run(
        ["docker", "cp", str(skill_path), f"{container_name}:{dest_dir}/SKILL.md"],
        capture_output=True, timeout=10
    )
    return skill_name, host_kb


def _read_token_usage(container_name: str) -> dict:
    """
    Legge /workspace/.token_usage dal container (scritto dal target agent dopo
    ogni turno) e ritorna {input_tokens, output_tokens, total_tokens, calls,
    cost, providers}. Tutti zero/vuoti se il file manca o non è leggibile (es.
    attempt skipped/errore, o provider non-OpenRouter — cost/providers restano
    0.0/{} in quel caso, vedi docker/run_agent.py:_write_token_usage).
    """
    zero = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0,
            "cost": 0.0, "providers": {}}
    try:
        r = subprocess.run(
            ["docker", "exec", container_name, "cat", "/workspace/.token_usage"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0 or not (r.stdout or "").strip():
            return zero
        data = json.loads(r.stdout)
        return {
            "input_tokens":  int(data.get("input_tokens") or 0),
            "output_tokens": int(data.get("output_tokens") or 0),
            "total_tokens":  int(data.get("total_tokens")
                                 or (int(data.get("input_tokens") or 0)
                                     + int(data.get("output_tokens") or 0))),
            "calls":         int(data.get("calls") or 0),
            "cost":          float(data.get("cost") or 0.0),
            "providers":     data.get("providers") or {},
        }
    except Exception:
        return zero


def run_target(
    skill_path:   str,
    user_prompt:  str,
    docker_image: str = "sse3-target",
    vuln_type:    str = "",
    container_name: str = "sse3-agent",
) -> tuple[str, list[str], str, dict]:
    """
    Esegue il target agent nello specifico container via docker exec.
    Molto più veloce del cold start — non c'è boot overhead.

    Args:
        skill_path:     path al SKILL.md (viene copiato nel container)
        user_prompt:    prompt da inviare all'agente
        docker_image:   usato solo se il container legacy non è ancora avviato
        vuln_type:      per timeout dinamico
        container_name: container target. Default "sse3-agent" (legacy/pool-di-1);
                        i pool passano "sse3-agent-<i>".

    Returns:
        (agent_stdout, tool_call_log, kb_info_line, token_usage)
        kb_info_line: "[KnowledgeBase] Loaded: /path (N chars, md5=...)" o "".
        token_usage:  {input_tokens, output_tokens, total_tokens, calls} del
                      target agent per questo attempt (zero se non disponibile).
    """
    global _container_id

    # Auto-start SOLO per il container legacy "sse3-agent". I container del pool
    # hanno ciclo di vita gestito da start_container_pool() e sono già attivi.
    if container_name == _container_name and not _container_id:
        start_container(docker_image)

    # Copia il SKILL.md nel container e ottieni la riga KB host-side (fallback)
    skill_name, host_kb = set_skill(skill_path, container_name)
    timeout    = _TIMEOUT_BY_VULN.get(vuln_type, _DEFAULT_TIMEOUT)

    # Workspace pulito allo snapshot dell'EnvAgent prima di ogni tentativo:
    # rimuove i file lasciati dal tentativo precedente.
    reset_workspace(container_name)

    cmd = [
        "docker", "exec",
        container_name,
        "python", "-u", "/app/run_agent.py",
        "--skill",  skill_name,
        "--prompt", user_prompt,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        stdout     = (result.stdout or "").strip()
        stderr_str = result.stderr or ""
        tool_calls = _extract_tool_calls(stderr_str)
        kb_info    = _extract_kb_info(stderr_str)

        if not stdout and stderr_str:
            first_lines = "\n".join(stderr_str.splitlines()[:5])
            cli.debug(f"   ⚠️  [Docker] no stdout. stderr: {first_lines[:200]}")

        return stdout, tool_calls, (kb_info or host_kb), _read_token_usage(container_name)

    except subprocess.TimeoutExpired:
        cli.debug(f"   ⏱️  [Docker] exec timeout ({timeout}s)"
                  + (" — possibile resource_exhaustion" if vuln_type == "resource_exhaustion" else ""))
        # Anche su timeout l'agente ha già scritto l'usage parziale dopo ogni turno.
        return ("[TIMEOUT]", ["TIMEOUT — container exec killed after executing command"],
                host_kb, _read_token_usage(container_name))

    except Exception as e:
        return f"[ERROR] {e}", [], host_kb, {"input_tokens": 0, "output_tokens": 0,
                                             "total_tokens": 0, "calls": 0}


def _extract_kb_info(stderr: str) -> str:
    """Estrae la riga '[KnowledgeBase] Loaded: ...' dallo stderr del target."""
    for line in stderr.splitlines():
        s = line.strip()
        if s.startswith("[KnowledgeBase] Loaded:"):
            return s
    return ""


def _extract_tool_calls(stderr: str) -> list[str]:
    return [
        line.strip() for line in stderr.splitlines()
        if line.strip().startswith(("TOOL_CALL:", "TOOL_RESULT:", "[Agent]"))
    ]
