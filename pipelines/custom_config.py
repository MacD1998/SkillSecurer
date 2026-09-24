"""
Schema + validator della pipeline custom (5ª modalità).
=======================================================
Una pipeline custom compone a runtime una combinazione valida dei 4 step
esistenti (fonte skill → difesa → eval → tester). Lo schema è in dataclass
(coerente con lo stile del progetto: TypedDict/dataclass, niente pydantic), con
round-trip JSON per la persistenza dei preset e un validatore che applica la
matrice di validità — gate "duro" lato backend, indipendente dalla UI.

Lo step di DIFESA è una SELEZIONE di motori (DefenseConfig.engines), non più il
solo Blue con i motori terzi come add-on: si può eseguire un giro col solo Blue,
uno col solo SkillSpector, uno col solo Cisco, o qualunque combinazione. Il
confronto fra motori NON avviene più dentro la run — è un post-processing
separato che mette a confronto run diverse.

Matrice di validità (vedi README §Custom pipeline):

  | source            | difesa       | eval | tester mode | scope                |
  |-------------------|--------------|------|-------------|----------------------|
  | red               | con 'blue'   | opz. | three-way   | all / blue_gap_only  |
  | red               | senza 'blue' | NO   | two-way*    | all                  |
  | skill_inject      | con 'blue'   | opz. | three-way   | all / blue_gap_only  |
  | skill_inject      | senza 'blue' | NO   | two-way*    | all                  |
  | local_preinjected | con 'blue'   | opz.†| three-way   | all / blue_gap_only  |
  | local_preinjected | senza 'blue' | NO   | two-way*    | all                  |
  | online            | qualsiasi    | NO   | two-way*    | all                  |

  (†) local_preinjected: l'eval è ammesso SOLO se la cartella contiene un file
      JSON di ground truth (mappa nome-file → testo injection). Senza quel JSON
      la ground truth non è nota e l'eval resta bloccato (come 'online').
  (*) two-way ammesso solo con difesa VUOTA (nessun motore). Una difesa di soli
      motori terzi + tester è bloccata: vedi la regola sul tester qui sotto.

Regole derivate:
  • eval ammesso  ⇔ 'blue' ∈ engines AND (source ∈ {red, skill_inject}  OR
                    (source=local_preinjected con JSON ground truth nella cartella)).
    L'eval resta esclusiva del Blue: i motori terzi non producono le quote testuali
    su cui si regge il match con la ground truth, e non patchano.
  • tester three-way ⇔ 'blue' ∈ engines (la FIXED viene dalla patch del Blue).
  • tester con difesa NON vuota ma SENZA 'blue' → BLOCCATO: i motori terzi non
    patchano, quindi non esiste una FIXED da testare e un tester two-way non
    misurerebbe nulla di quella difesa. Il tester two-way resta ammesso solo con
    difesa completamente vuota (misura la sola INJECTED, come prima).
  • tester_scope="blue_gap_only" ha senso solo con 'blue' ∈ engines.
  • difesa/eval/tester possono essere tutti vuoti/false (caso valido, di scarsa
    utilità: produce solo le skill iniettate secondo la fonte).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


# ── Domini ─────────────────────────────────────────────────────────────
SOURCE_TYPES         = ("red", "skill_inject", "local_preinjected", "online")
# Fonti con ground truth nota → unica condizione (con blue) in cui l'eval è ammesso.
GROUND_TRUTH_SOURCES = ("red", "skill_inject")
# Motori di difesa selezionabili. "blue" è il nostro; gli altri sono motori terzi
# eseguiti come difesa a sé stante (non più come "confronto" agganciato al Blue).
# L'ordine è quello canonico di esecuzione/visualizzazione.
DEFENSE_ENGINES      = ("blue", "skillspector", "cisco", "aig", "skill_vetter", "snyk", "skills_sh")
# Sottoinsieme di DEFENSE_ENGINES che supporta un'analisi LLM opzionale, quindi
# un override "solo-statico" (DefenseConfig.no_llm) — per confrontare i
# risultati con/senza LLM a parità di skill (vedi agents/skillspector_scanner.py,
# agents/cisco_scanner.py).
NO_LLM_ENGINES       = ("skillspector", "cisco")
SKILL_INJECT_CATEGORIES = ("obvious", "contextual")
TESTER_SCOPES        = ("all", "blue_gap_only")
RED_DIFFICULTIES     = ("K1", "K2", "K3")
RED_VULN_TYPES       = ("arbitrary_script_execution", "data_exfiltration", "supply_chain",
                        "credential_exposure", "prompt_hijacking", "resource_exhaustion",
                        "privilege_escalation", "indirect_injection", "guardfall")


# ── Ground truth per la fonte local_preinjected ────────────────────────

def _looks_like_ground_truth(data: dict) -> bool:
    """Valida che il dict sia plausibilmente una mappa nome-file→injection
    (non un config/report qualsiasi che capita a essere un dict non vuoto).
    Richiede che almeno metà delle chiavi assomigli a un nome di file skill
    (es. *.md)."""
    if not data:
        return False
    keys = [k for k in data if isinstance(k, str)]
    if not keys:
        return False
    filelike = sum(1 for k in keys if k.lower().endswith((".md", ".markdown")))
    return filelike / len(keys) >= 0.5


def find_ground_truth_json(folder_path: Optional[str]) -> Optional[str]:
    """Cerca nella cartella locale (e nel suo primo livello di sottocartelle,
    es. injected/) un JSON di ground truth (mappa nome-file → injection).
    Ritorna il path del primo JSON valido, oppure None. Un JSON è valido solo
    se il dict non è vuoto E le sue chiavi assomigliano a nomi di file skill
    (altrimenti un config/report qualsiasi verrebbe scambiato per ground
    truth). Preferisce i file il cui nome richiama la ground truth
    (es. ground_truth.json, injections.json). Sola I/O di lettura, nessun side
    effect: usabile sia dal validatore (gate eval) sia dal loader della fonte."""
    if not (folder_path or "").strip():
        return None
    folder = Path(folder_path)
    if not folder.is_dir():
        return None

    def rank(p: Path) -> tuple:
        n = p.name.lower()
        hinted = any(k in n for k in ("ground", "truth", "inject"))
        return (0 if hinted else 1, n)

    candidates = list(folder.glob("*.json")) + list(folder.glob("*/*.json"))
    for p in sorted(candidates, key=rank):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and _looks_like_ground_truth(data):
            return str(p)
    return None


# ── Dataclass ──────────────────────────────────────────────────────────

@dataclass
class SourceConfig:
    type: str
    # red / local_preinjected: cartella + selezione multi-file.
    local_folder_path: Optional[str] = None
    selected_files: Optional[List[str]] = None
    # red: difficoltà delle injection da generare (subset di {K1,K2,K3}; None/[] = tutte).
    red_difficulties: Optional[List[str]] = None
    # red: tipologie di vulnerabilità da generare (subset delle 8; None/[] = tutte).
    red_vuln_types: Optional[List[str]] = None
    # red: profilo skill-inject. Se True, il Red usa la tassonomia a 8 classi del
    # paper (config/catalog_paper.json) e le injection direct di skill-inject come
    # KB di esempi (mai copiati). Flag unico, accoppiato: catalog paper + KB insieme.
    use_skill_inject_kb: bool = False
    # skill_inject: categorie {obvious, contextual} + filtro per skill-file
    # (es. docx, pptx, calendar; None/[] = tutte le skill delle categorie scelte).
    skill_inject_categories: Optional[List[str]] = None
    skill_inject_skills: Optional[List[str]] = None
    # skill_inject: root del repo skill-inject (relativo alla repo root se non
    # assoluto). None/"" → default "skill-inject" (stesso default di --skill-inject-path).
    skill_inject_path: Optional[str] = None
    # online: una o più URL.
    urls: Optional[List[str]] = None


@dataclass
class DefenseConfig:
    """Step di difesa: quali motori eseguire su ogni skill.

    Un motore vale l'altro dal punto di vista dello step — sono difese alternative,
    non "il Blue più dei comparatori". Selezionarne più di uno nella stessa run è
    ammesso (li esegue tutti sullo stesso input), ma il confronto fra i loro
    verdetti NON viene più prodotto qui: si fa a posteriori fra run diverse.

    'blue' è l'unico motore che patcha e l'unico su cui girano eval e tester —
    vedi la matrice di validità nel docstring del modulo.

    no_llm: sottoinsieme di `engines` ∩ NO_LLM_ENGINES da eseguire forzando lo
    scan solo-statico anche con credenziali LLM disponibili — per confrontare i
    risultati con/senza LLM a parità di skill nella stessa run. Un motore in
    no_llm ma non in engines è un no-op silenzioso (il motore non gira affatto),
    non un errore: coerente con l'idea che i flag CLI --with-* sono additivi.
    """
    engines: List[str] = field(default_factory=list)
    no_llm:  List[str] = field(default_factory=list)

    @property
    def enabled(self) -> bool:
        """True se almeno un motore è selezionato (lo step di difesa gira)."""
        return bool(self.engines)

    def has(self, engine: str) -> bool:
        return engine in (self.engines or [])

    @property
    def has_blue(self) -> bool:
        return self.has("blue")

    def no_llm_for(self, engine: str) -> bool:
        return engine in (self.no_llm or [])


# Chiavi legacy "blue.with_*" → id motore, per i preset salvati prima che la
# difesa diventasse una selezione (vedi _defense_from_dict).
_LEGACY_WITH_KEYS = (("with_skillspector", "skillspector"),
                     ("with_cisco",        "cisco"),
                     ("with_snyk",         "snyk"),
                     ("with_skills_sh",    "skills_sh"))


def clean_no_llm(no_llm) -> List[str]:
    """Normalizza la lista no_llm come clean_engines: scarta i non-stringa,
    deduplica e riordina secondo NO_LLM_ENGINES. I valori sconosciuti restano
    (li segnala validate_config, stesso principio di clean_engines)."""
    seen = [str(e).strip() for e in (no_llm or []) if str(e or "").strip()]
    known = [e for e in NO_LLM_ENGINES if e in seen]
    unknown = [e for e in dict.fromkeys(seen) if e not in NO_LLM_ENGINES]
    return known + unknown


def _defense_from_dict(d: dict) -> "DefenseConfig":
    """Costruisce la DefenseConfig da un dict di preset, accettando i due
    formati storici oltre a quello corrente:

      • corrente:  {"defense": {"engines": ["blue", "cisco"]}}
      • legacy 2:  {"blue": {"enabled": true, "with_cisco": true, ...}}
      • legacy 1:  {"blue": true}

    Nei formati legacy i motori terzi erano add-on del Blue e non giravano se il
    Blue era spento: la conversione rispetta quel gate, altrimenti un preset con
    blue disabilitato e un with_* residuo comincerebbe a eseguire uno scan che
    prima non faceva.
    """
    raw = d.get("defense")
    if isinstance(raw, dict):
        return DefenseConfig(engines=clean_engines(raw.get("engines")),
                              no_llm=clean_no_llm(raw.get("no_llm")))

    blue_raw = d.get("blue", False)
    if isinstance(blue_raw, dict):
        if not blue_raw.get("enabled", False):
            return DefenseConfig(engines=[])
        engines = ["blue"] + [eng for key, eng in _LEGACY_WITH_KEYS if blue_raw.get(key)]
        return DefenseConfig(engines=clean_engines(engines))
    return DefenseConfig(engines=["blue"] if blue_raw else [])


def clean_engines(engines) -> List[str]:
    """Normalizza la lista motori: scarta i non-stringa, deduplica e riordina
    secondo DEFENSE_ENGINES. I valori sconosciuti NON vengono scartati qui — li
    segnala validate_config, altrimenti un id sbagliato sparirebbe in silenzio."""
    seen = [str(e).strip() for e in (engines or []) if str(e or "").strip()]
    known = [e for e in DEFENSE_ENGINES if e in seen]
    unknown = [e for e in dict.fromkeys(seen) if e not in DEFENSE_ENGINES]
    return known + unknown


@dataclass
class TesterConfig:
    enabled: bool = False
    scope: Optional[str] = None   # "all" | "blue_gap_only" | None (tester off / difesa senza blue)
    # True (default): prompt orientati alla sezione iniettata (injection-aware).
    # False: prompt generati alla cieca dalla sola BASE. In entrambi i casi i prompt
    # restano richieste di un utente bene-intenzionato.
    injection_aware: bool = True


@dataclass
class PipelineConfig:
    name: str
    source: SourceConfig
    defense: DefenseConfig = field(default_factory=DefenseConfig)
    # `eval` è builtin in Python → campo interno `eval_enabled`, serializzato come
    # "eval" nel JSON (vedi to_dict/from_dict) per restare fedele allo schema della tesi.
    eval_enabled: bool = False
    tester: TesterConfig = field(default_factory=TesterConfig)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # ── Round-trip JSON ────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "source":     asdict(self.source),
            "defense":    asdict(self.defense),
            "eval":       bool(self.eval_enabled),
            "tester":     asdict(self.tester),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineConfig":
        src = d.get("source") or {}
        tst = d.get("tester") or {}
        defense = _defense_from_dict(d)
        return cls(
            name=         (d.get("name") or "").strip(),
            source=       SourceConfig(
                type=                    src.get("type", ""),
                local_folder_path=       src.get("local_folder_path"),
                selected_files=          src.get("selected_files"),
                red_difficulties=        src.get("red_difficulties"),
                red_vuln_types=          src.get("red_vuln_types"),
                use_skill_inject_kb=     bool(src.get("use_skill_inject_kb", False)),
                skill_inject_categories= src.get("skill_inject_categories"),
                skill_inject_skills=     src.get("skill_inject_skills"),
                skill_inject_path=       src.get("skill_inject_path"),
                urls=                    src.get("urls"),
            ),
            defense=      defense,
            eval_enabled= bool(d.get("eval", False)),
            tester=       TesterConfig(
                enabled=         bool(tst.get("enabled", False)),
                scope=           tst.get("scope"),
                injection_aware= bool(tst.get("injection_aware", True)),
            ),
            created_at=   d.get("created_at"),
            updated_at=   d.get("updated_at"),
        )

    def touch(self, *, creating: bool) -> None:
        """Aggiorna created_at/updated_at (ISO UTC) per la lista preset."""
        now = datetime.now(timezone.utc).isoformat()
        if creating and not self.created_at:
            self.created_at = now
        self.updated_at = now


# ── Normalizzazione ────────────────────────────────────────────────────

def normalize(cfg: PipelineConfig) -> PipelineConfig:
    """Riempie i default impliciti PRIMA della validazione/esecuzione:
      • skill_inject senza categorie → entrambe;
      • motori di difesa deduplicati e riordinati (ordine canonico);
      • tester abilitato senza scope → "all";
      • tester senza 'blue' fra i motori → scope forzato "all" (no FIXED, no "gap");
      • tester disabilitato → scope=None.
    Non modifica nulla di semanticamente ambiguo: quello lo blocca validate_config.
    """
    s = cfg.source
    if s.type == "skill_inject" and not s.skill_inject_categories:
        s.skill_inject_categories = list(SKILL_INJECT_CATEGORIES)
    cfg.defense.engines = clean_engines(cfg.defense.engines)
    cfg.defense.no_llm  = clean_no_llm(cfg.defense.no_llm)
    if cfg.tester.enabled:
        if not cfg.defense.has_blue:
            cfg.tester.scope = "all"          # two-way → niente blue_gap
        elif not cfg.tester.scope:
            cfg.tester.scope = "all"
    else:
        cfg.tester.scope = None
    return cfg


# ── Validazione (matrice di validità) ──────────────────────────────────

def validate_config(cfg: PipelineConfig) -> List[str]:
    """Ritorna la lista (eventualmente vuota) degli errori. Applica ESATTAMENTE
    la matrice di validità. Pensata per: gate backend (validate_or_raise) e
    riuso lato UI per messaggi coerenti."""
    errs: List[str] = []

    if not (cfg.name or "").strip():
        errs.append("name: il preset deve avere un nome non vuoto.")

    s = cfg.source
    if s.type not in SOURCE_TYPES:
        errs.append(f"source.type: '{s.type}' non valido (atteso uno di {SOURCE_TYPES}).")
        return errs  # senza una fonte valida il resto non è verificabile

    # ── Campi specifici per fonte ──────────────────────────────────────
    if s.type in ("red", "local_preinjected"):
        if not (s.local_folder_path or "").strip():
            errs.append(f"source.local_folder_path: richiesto per la fonte '{s.type}'.")
        if not s.selected_files:
            errs.append(f"source.selected_files: seleziona almeno un file per la fonte '{s.type}'.")
        if s.type == "red" and s.red_difficulties:
            bad = [d for d in s.red_difficulties if str(d).upper() not in RED_DIFFICULTIES]
            if bad:
                errs.append(f"source.red_difficulties: valori non validi {bad} (ammessi {RED_DIFFICULTIES}).")
        if s.type == "red" and s.red_vuln_types:
            bad = [v for v in s.red_vuln_types if str(v).lower() not in RED_VULN_TYPES]
            if bad:
                errs.append(f"source.red_vuln_types: valori non validi {bad} (ammessi {RED_VULN_TYPES}).")
    elif s.type == "skill_inject":
        cats = s.skill_inject_categories or []
        bad = [c for c in cats if c not in SKILL_INJECT_CATEGORIES]
        if bad:
            errs.append(f"source.skill_inject_categories: valori non validi {bad} "
                        f"(ammessi {SKILL_INJECT_CATEGORIES}).")
        # skill_inject_skills è opzionale (None/[] = tutte le skill delle categorie).
    elif s.type == "online":
        urls = [u for u in (s.urls or []) if (u or "").strip()]
        if not urls:
            errs.append("source.urls: fornisci almeno una URL per la fonte 'online'.")
        bad = [u for u in urls if not u.strip().lower().startswith(("http://", "https://"))]
        if bad:
            errs.append(f"source.urls: URL non http(s): {bad}.")

    # ── Difesa (motori selezionati) ────────────────────────────────────
    bad_engines = [e for e in (cfg.defense.engines or []) if e not in DEFENSE_ENGINES]
    if bad_engines:
        errs.append(f"defense.engines: motori non validi {bad_engines} "
                    f"(ammessi {DEFENSE_ENGINES}).")
    bad_no_llm = [e for e in (cfg.defense.no_llm or []) if e not in NO_LLM_ENGINES]
    if bad_no_llm:
        errs.append(f"defense.no_llm: motori non validi {bad_no_llm} "
                    f"(ammessi {NO_LLM_ENGINES} — solo i motori con analisi LLM opzionale).")

    # ── Eval (ground truth nota + qualcosa da valutare) ────────────────
    if cfg.eval_enabled:
        if s.type in GROUND_TRUTH_SOURCES:
            pass  # ground truth generata dalla fonte stessa
        elif s.type == "local_preinjected":
            # Sbloccato solo se la cartella porta un JSON di ground truth.
            if not find_ground_truth_json(s.local_folder_path):
                errs.append("eval: per 'local_preinjected' serve un file JSON di ground "
                            "truth nella cartella (mappa nome-file → injection); "
                            "senza, la ground truth non è nota e l'eval è bloccato.")
        else:
            errs.append("eval: disponibile solo con fonte 'red'/'skill_inject', oppure "
                        "'local_preinjected' con JSON di ground truth; disabilitalo per "
                        "'online'.")
        if not cfg.defense.has_blue:
            errs.append("eval: richiede il motore di difesa 'blue' (valuta i suoi finding "
                        "contro il ground truth; i motori terzi non producono le quote "
                        "testuali su cui si regge il match).")

    # ── Tester scope ───────────────────────────────────────────────────
    t = cfg.tester
    if t.enabled:
        if t.scope is not None and t.scope not in TESTER_SCOPES:
            errs.append(f"tester.scope: '{t.scope}' non valido (ammessi {TESTER_SCOPES}).")
        if t.scope == "blue_gap_only" and not cfg.defense.has_blue:
            errs.append("tester.scope='blue_gap_only': richiede il motore di difesa 'blue' "
                        "(senza il suo output non esistono 'gap' da cui filtrare).")
        # Difesa di soli motori terzi + tester: nessuno di quei motori patcha,
        # quindi non c'è FIXED da testare e il two-way misurerebbe la INJECTED
        # senza dire nulla sulla difesa selezionata. Con difesa VUOTA il two-way
        # resta ammesso (è la misura della sola skill iniettata, come prima).
        if cfg.defense.enabled and not cfg.defense.has_blue:
            errs.append("tester: con una difesa di soli motori terzi "
                        f"({', '.join(cfg.defense.engines)}) non esiste una versione FIXED "
                        "da testare — quei motori rilevano ma non patchano. Aggiungi 'blue' "
                        "ai motori di difesa, oppure disabilita il tester.")
    elif t.scope not in (None, "all"):
        errs.append("tester.scope: impostato ma tester disabilitato.")

    return errs


def validate_or_raise(cfg: PipelineConfig) -> PipelineConfig:
    """Normalizza poi valida; alza ValueError con tutti gli errori se non valida.
    Unico gate "duro" usato da orchestratore, CLI e persistenza."""
    normalize(cfg)
    errs = validate_config(cfg)
    if errs:
        raise ValueError("Config pipeline custom non valida:\n  - " + "\n  - ".join(errs))
    return cfg
