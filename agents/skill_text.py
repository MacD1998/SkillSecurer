"""
Normalizzazione del frontmatter di una SKILL.md al CARICAMENTO
==============================================================
Alcune skill del dataset `skill-inject` arrivano con un frontmatter YAML che non
parsa, per un difetto upstream: manca lo spazio dopo i due punti.

    description:"\\"This skill calculates key financial ratios...\\""

YAML richiede `key: value`; senza spazio la riga viene letta come una chiave
`description:"\\"This` e il documento è invalido. Sono affette
analyzing-financial-statements, applying-brand-guidelines e
bats-testing-patterns — già nella versione PULITA, prima di qualunque injection.

Conseguenza a valle: ogni scanner che carica la skill come skill-dir (Cisco
skill-scanner in primis) fallisce l'intero scan del file, mentre Blue — che
legge testo grezzo e del YAML non si cura — lo processa normalmente. Nel
confronto Blue-vs-motori-terzi Blue prenderebbe così credito su file che i
concorrenti non riescono nemmeno a caricare: un bias a nostro favore.

Si normalizza IN MEMORIA al load, non su disco: `skill-inject/` è vendorato e la
sua fedeltà byte-per-byte regge il ground truth di `blue-eval` (il loader
ricostruisce i file iniettati esattamente come fa il dataset). Toccare i file
sorgente invaliderebbe quel confronto.
"""
from __future__ import annotations

import re

# Chiave a inizio riga, due punti, e SUBITO una virgoletta: `description:"...`.
# `[^\S\n]` invece di `\s` perche' un `\s*` matcherebbe anche il newline e
# andrebbe a pescare la riga successiva.
_KEY_NO_SPACE = re.compile(r'^([A-Za-z_][\w-]*):(?=["\'])', re.MULTILINE)

_FRONTMATTER = re.compile(r'^(---[^\S\n]*\n)(.*?)(\n---[^\S\n]*(?:\n|$))', re.DOTALL)


def normalize_frontmatter(content: str) -> str:
    """Inserisce lo spazio mancante dopo `key:` nel frontmatter YAML.

    Agisce SOLO dentro il blocco `---...---` iniziale: nel corpo markdown una
    sequenza come `nota:"testo"` è testo legittimo e non va toccata. Se non c'è
    frontmatter, o non c'è nulla da correggere, ritorna `content` invariato
    (stesso oggetto stringa quando possibile) — così la normalizzazione è
    trasparente per tutte le skill già valide, che sono la quasi totalità.
    """
    m = _FRONTMATTER.match(content)
    if not m:
        return content
    block = m.group(2)
    fixed = _KEY_NO_SPACE.sub(r"\1: ", block)
    if fixed == block:
        return content
    return m.group(1) + fixed + m.group(3) + content[m.end():]
