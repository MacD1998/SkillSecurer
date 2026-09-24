"""Genera pagine HTML standalone per la validazione manuale dei finding di Blue.

Ogni skill flaggata (con almeno un finding) viene assegnata a `coverage` validatori
su un totale di `n_validators`, con un pattern round-robin (escludi il validatore
`indice_skill % n_validators`, in ordine di skill id) cosi' il carico resta
bilanciato e ogni finding viene rivisto da piu' persone in modo incrociato.

Le pagine sono completamente self-contained (nessuna dipendenza esterna): stato
di conferma/note salvato in localStorage, con export a JSON via bottone.

Uso:
    python3 -m postprocess.finding_validation \\
        --run results/examples/skilltrustbench_130_likely_benign/webui_run_skillTrustBench_130_Sonnet \\
        --engine blue \\
        --out results/examples/skilltrustbench_130_likely_benign/webui_run_skillTrustBench_130_Sonnet/validation \\
        --run-key skillTrustBench130_Sonnet
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_GROUND_TRUTH = Path(__file__).resolve().parent.parent / "dataset" / "SkillTrustBench" / "secureSkills" / "ground_truth.json"


def _load_categories() -> dict[str, str]:
    if not _GROUND_TRUTH.is_file():
        return {}
    data = json.loads(_GROUND_TRUTH.read_text(encoding="utf-8"))
    return {c["id"]: c.get("base_category", "—") for c in data.get("test_cases", [])}


def build_cases(run_dir: Path, engine: str) -> list[dict]:
    """Estrae dal results.json della run le skill flaggate da `engine`, ordinate per id."""
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8", errors="ignore"))
    categories = _load_categories()
    cases = []
    for rec in results.get("findings_detail", []):
        eng = (rec.get("engines") or {}).get(engine) or {}
        if not eng.get("flagged"):
            continue
        findings = rec.get("findings") or []
        cases.append({
            "skill": rec["skill"],
            "category": categories.get(rec["skill"], "—"),
            "detected": True,
            "findings": [
                {"fid": i, "type": f.get("type"), "severity": f.get("severity"),
                 "description": f.get("description"), "quote": f.get("quote")}
                for i, f in enumerate(findings)
            ],
            "skill_md": rec.get("skill_content_injected") or "",
            "patch_failed": bool(rec.get("patch_failed")),
            "patch_reasoning": rec.get("patch_reasoning"),
            "patches_applied": rec.get("patches_applied") or [],
            "skill_md_fixed": rec.get("skill_content_fixed"),
        })
    cases.sort(key=lambda c: c["skill"])
    return cases


def assign_validators(cases: list[dict], n_validators: int, coverage: int) -> list[list[dict]]:
    """Round-robin: la skill all'indice i esclude il validatore i % n_validators.

    Con coverage = n_validators - 1 ogni skill finisce esattamente su `coverage`
    validatori, bilanciati il piu' possibile (chi viene escluso meno volte
    riceve piu' skill).
    """
    if coverage != n_validators - 1:
        raise ValueError("assign_validators supporta solo coverage == n_validators - 1 (esclusione singola round-robin)")
    buckets = [[] for _ in range(n_validators)]
    for i, c in enumerate(cases):
        excluded = i % n_validators
        for v in range(n_validators):
            if v != excluded:
                buckets[v].append(c)
    return buckets


_CSS = """
  :root { color-scheme: light; }
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#f8fafc; color:#0f172a; margin:0; }
  header { position:sticky; top:0; background:white; border-bottom:1px solid #e2e8f0; padding:14px 24px; z-index:10; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  header h1 { font-size:16px; margin:0; }
  header .sub { font-size:12px; color:#64748b; }
  #progress { font-size:13px; color:#334155; }
  #progress b { color:#0f172a; }
  #export-btn { margin-left:auto; background:#0f172a; color:white; border:none; border-radius:8px; padding:8px 16px; font-size:13px; cursor:pointer; }
  #export-btn:hover { background:#1e293b; }
  #validator-name { border:1px solid #cbd5e1; border-radius:6px; padding:6px 10px; font-size:13px; }
  main { max-width:980px; margin:0 auto; padding:20px 24px 80px; }
  .case { background:white; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:14px; overflow:hidden; }
  .case.done { border-color:#86efac; }
  .case summary { cursor:pointer; padding:12px 16px; display:flex; gap:12px; align-items:center; list-style:none; }
  .case summary::-webkit-details-marker { display:none; }
  .case[open] summary { border-bottom:1px solid #e2e8f0; background:#f8fafc; }
  .skill { font-family: ui-monospace, monospace; font-weight:600; font-size:13px; }
  .cat { background:#e0e7ff; color:#3730a3; font-size:11px; padding:2px 8px; border-radius:999px; }
  .badge-detected { font-size:11px; padding:2px 8px; border-radius:999px; }
  .badge-yes { background:#fee2e2; color:#991b1b; }
  .badge-no { background:#dcfce7; color:#166534; }
  .status-chip { margin-left:auto; font-size:11px; padding:2px 10px; border-radius:999px; background:#e2e8f0; color:#475569; }
  .status-chip.on { background:#22c55e; color:white; }
  .body { padding:14px 16px; }
  .section-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.03em; color:#0369a1; margin:10px 0 6px; }
  .finding { border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; margin-bottom:10px; }
  .finding.reviewed-confirmed { border-color:#86efac; background:#f0fdf4; }
  .finding-head { display:flex; gap:8px; align-items:center; margin-bottom:4px; }
  .type { font-weight:600; font-size:13px; }
  .sev { color:white; font-size:10px; padding:1px 8px; border-radius:999px; text-transform:uppercase; }
  .sev-high { background:#dc2626; } .sev-medium { background:#d97706; } .sev-low { background:#65a30d; }
  .desc { font-size:13px; color:#334155; line-height:1.5; }
  .quote { background:#0f172a; color:#e2e8f0; font-size:11px; padding:8px 10px; border-radius:6px; margin-top:6px; overflow-x:auto; white-space:pre-wrap; }
  .skillmd { border:1px dashed #cbd5e1; border-radius:6px; margin-top:10px; }
  .skillmd summary { padding:6px 10px; font-size:12px; color:#475569; cursor:pointer; }
  .skillmd-body { background:#f8fafc; border-top:1px dashed #cbd5e1; font-size:11px; padding:10px; margin:0; white-space:pre-wrap; max-height:340px; overflow-y:auto; }
  .patch-section { margin-top:14px; border-top:1px solid #e2e8f0; padding-top:12px; }
  .patch-fail { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; border-radius:6px; padding:6px 10px; font-size:12px; margin-bottom:8px; }
  .patch-reasoning { font-size:13px; color:#334155; line-height:1.5; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:10px; margin-bottom:10px; }
  .patch-diff { border:1px solid #e2e8f0; border-radius:6px; margin-bottom:8px; overflow:hidden; }
  .patch-diff-reason { font-size:11px; color:#64748b; padding:6px 10px; background:#f8fafc; border-bottom:1px solid #e2e8f0; }
  .patch-diff-body { display:grid; grid-template-columns:1fr 1fr; }
  .patch-orig, .patch-repl { font-size:11px; padding:8px 10px; white-space:pre-wrap; margin:0; overflow-x:auto; }
  .patch-orig { background:#fef2f2; color:#7f1d1d; border-right:1px solid #e2e8f0; }
  .patch-repl { background:#f0fdf4; color:#14532d; }
  .review-row { margin-top:10px; display:flex; flex-direction:column; gap:6px; }
  .review-checkbox { display:flex; align-items:center; gap:6px; font-size:13px; font-weight:600; cursor:pointer; }
  .review-checkbox input[type=checkbox] { width:16px; height:16px; }
  textarea.fnotes { width:100%; box-sizing:border-box; min-height:48px; border:1px solid #cbd5e1; border-radius:6px; padding:8px; font-size:12px; font-family:inherit; resize:vertical; }
  footer { text-align:center; font-size:12px; color:#94a3b8; padding:20px; }
"""

_JS = r"""
(function() {
  const RUN_KEY = %(run_key)s;
  const cases = JSON.parse(document.getElementById('cases-data').textContent);
  const app = document.getElementById('app');
  const progressCount = document.getElementById('progress-count');
  const validatorName = document.getElementById('validator-name');
  const totalFindings = cases.reduce(function(n, c) { return n + c.findings.length; }, 0);

  function storageKey(skill, fid) { return 'stb_validate__' + RUN_KEY + '__' + skill + '__f' + fid; }

  function loadState(skill, fid) {
    let s;
    try { s = JSON.parse(localStorage.getItem(storageKey(skill, fid)) || 'null'); }
    catch (e) { s = null; }
    if (!s || typeof s !== 'object') s = {confirmed: false, notes: ''};
    s.confirmed = !!s.confirmed;
    s.notes = s.notes || '';
    return s;
  }
  function saveState(skill, fid, state) {
    localStorage.setItem(storageKey(skill, fid), JSON.stringify(state));
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function findingHtml(c, f) {
    const sevClass = 'sev-' + (f.severity || 'low').toLowerCase();
    return '<div class="finding" data-skill="' + esc(c.skill) + '" data-fid="' + f.fid + '">' +
      '<div class="finding-head"><span class="type">' + esc(f.type) + '</span>' +
      '<span class="sev ' + sevClass + '">' + esc(f.severity || '—') + '</span></div>' +
      '<div class="desc">' + esc(f.description) + '</div>' +
      (f.quote ? '<pre class="quote">' + esc(f.quote) + '</pre>' : '') +
      '<div class="review-row">' +
        '<label class="review-checkbox"><input type="checkbox" data-confirm> Confirmed</label>' +
        '<textarea class="fnotes" data-fnotes placeholder="Note (optional)"></textarea>' +
      '</div>' +
    '</div>';
  }

  function diffHtml(p) {
    return '<div class="patch-diff">' +
      (p.reason ? '<div class="patch-diff-reason">' + esc(p.reason) + '</div>' : '') +
      '<div class="patch-diff-body">' +
        '<pre class="patch-orig">− ' + esc(p.original) + '</pre>' +
        '<pre class="patch-repl">+ ' + esc(p.replacement) + '</pre>' +
      '</div>' +
    '</div>';
  }

  function patchSectionHtml(c) {
    if (!c.patch_reasoning && !c.patches_applied.length && !c.skill_md_fixed) return '';
    return '<div class="patch-section">' +
      '<div class="section-label">Patch applied by Blue</div>' +
      (c.patch_failed ? '<div class="patch-fail">⚠ patch_failed = true</div>' : '') +
      (c.patch_reasoning ? '<div class="patch-reasoning">' + esc(c.patch_reasoning) + '</div>' : '') +
      c.patches_applied.map(diffHtml).join('') +
      (c.skill_md_fixed ? (
        '<details class="skillmd"><summary>SKILL.md after patch (' + c.skill_md_fixed.length + ' chars)</summary>' +
          '<pre class="skillmd-body">' + esc(c.skill_md_fixed) + '</pre>' +
        '</details>'
      ) : '') +
    '</div>';
  }

  function updateProgress() {
    let n = 0;
    for (const c of cases) for (const f of c.findings) if (loadState(c.skill, f.fid).confirmed) n++;
    progressCount.textContent = n;
  }

  function render() {
    app.innerHTML = cases.map(function(c) {
      return (
        '<details class="case" data-skill="' + esc(c.skill) + '">' +
          '<summary>' +
            '<span class="skill">' + esc(c.skill) + '</span>' +
            '<span class="cat">' + esc(c.category || '—') + '</span>' +
            '<span class="badge-detected ' + (c.detected ? 'badge-yes' : 'badge-no') + '">' +
              (c.detected ? 'flagged' : 'not flagged') + '</span>' +
            '<span class="status-chip" data-chip>0/' + c.findings.length + ' confirmed</span>' +
          '</summary>' +
          '<div class="body">' +
            '<div class="section-label">Blue findings (' + c.findings.length + ')</div>' +
            c.findings.map(function(f) { return findingHtml(c, f); }).join('') +
            '<details class="skillmd"><summary>SKILL.md scanned (' + c.skill_md.length + ' chars)</summary>' +
              '<pre class="skillmd-body">' + esc(c.skill_md) + '</pre>' +
            '</details>' +
            patchSectionHtml(c) +
          '</div>' +
        '</details>'
      );
    }).join('');

    app.querySelectorAll('.case').forEach(function(caseEl) {
      const skill = caseEl.getAttribute('data-skill');
      const chip = caseEl.querySelector('[data-chip]');
      const findingEls = caseEl.querySelectorAll('.finding');
      const nFindings = findingEls.length;

      function refreshChip() {
        let done = 0;
        findingEls.forEach(function(fe) {
          const fid = fe.getAttribute('data-fid');
          if (loadState(skill, fid).confirmed) done++;
        });
        chip.textContent = done + '/' + nFindings + ' confirmed';
        chip.classList.toggle('on', done === nFindings);
        caseEl.classList.toggle('done', done === nFindings);
      }

      findingEls.forEach(function(fe) {
        const fid = fe.getAttribute('data-fid');
        const cb = fe.querySelector('[data-confirm]');
        const notes = fe.querySelector('[data-fnotes]');
        const state = loadState(skill, fid);
        cb.checked = !!state.confirmed;
        notes.value = state.notes || '';
        fe.classList.toggle('reviewed-confirmed', !!state.confirmed);

        cb.addEventListener('change', function() {
          const s = loadState(skill, fid);
          s.confirmed = cb.checked;
          saveState(skill, fid, s);
          fe.classList.toggle('reviewed-confirmed', cb.checked);
          refreshChip(); updateProgress();
        });
        notes.addEventListener('input', function() {
          const s = loadState(skill, fid);
          s.notes = notes.value;
          saveState(skill, fid, s);
        });
      });

      refreshChip();
    });

    updateProgress();
  }

  render();

  document.getElementById('export-btn').addEventListener('click', function() {
    const skills = cases.map(function(c) {
      const findings = c.findings.slice().sort(function(a, b) { return a.fid - b.fid; }).map(function(f) {
        const s = loadState(c.skill, f.fid);
        return {
          finding_index: f.fid, type: f.type, severity: f.severity,
          confirmed: s.confirmed, notes: s.notes || ''
        };
      });
      return {skill: c.skill, category: c.category, findings: findings};
    });
    const out = {
      run: RUN_KEY,
      validator: validatorName.value || null,
      exported_at: new Date().toISOString(),
      total_findings: totalFindings,
      skills: skills
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    const nameSlug = (validatorName.value || 'export').trim().replace(/[^a-zA-Z0-9_-]+/g, '_');
    a.download = RUN_KEY + '__' + nameSlug + '.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
  });
})();
"""


def _js_json(obj) -> str:
    """JSON sicuro dentro un blocco <script>: ogni "<" diventa \\u003c.

    Vedi la stessa nota in postprocess/comparison_report.py: scappare solo
    "</" non basta perche' un "<!--" seguito da "<script" nei contenuti (es.
    SKILL.md con esempi HTML) manda il tokenizer HTML in "script data double
    escaped state" e un </script> legittimo piu' avanti non chiude piu' il
    tag, fondendo i blocchi script tra loro.
    """
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


def render_page(cases: list[dict], *, title: str, subtitle: str, run_key: str) -> str:
    n_findings = sum(len(c["findings"]) for c in cases)
    data_json = _js_json(cases)
    js = _JS % {"run_key": _js_json(run_key)}
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>{title}</h1>
    <div class="sub">{subtitle}</div>
  </div>
  <input id="validator-name" placeholder="Your name" />
  <div id="progress">Findings confirmed: <b id="progress-count">0</b> / {n_findings}</div>
  <button id="export-btn">Export results (JSON)</button>
</header>
<main id="app"></main>
<footer>Answers are saved locally in the browser (localStorage) &mdash; use "Export" to generate the file to send back. Each finding must be confirmed individually.</footer>

<script type="application/json" id="cases-data">{data_json}</script>
<script>{js}</script>
</body>
</html>
'''


def generate(run_dir: Path, out_dir: Path, *, engine: str = "blue",
             n_validators: int = 4, coverage: int | None = None,
             run_key: str | None = None) -> dict:
    coverage = coverage if coverage is not None else n_validators - 1
    run_key = run_key or run_dir.name
    cases = build_cases(run_dir, engine)
    n_findings = sum(len(c["findings"]) for c in cases)

    out_dir.mkdir(parents=True, exist_ok=True)

    all_title = f"{run_dir.name} — finding validation (all cases)"
    all_sub = f"{run_dir.name} · {len(cases)} skill · {n_findings} finding"
    (out_dir / "all_cases.html").write_text(
        render_page(cases, title=all_title, subtitle=all_sub, run_key=f"{run_key}_all"),
        encoding="utf-8")

    buckets = assign_validators(cases, n_validators, coverage)
    written = ["all_cases.html"]
    for i, bucket in enumerate(buckets, start=1):
        nb_findings = sum(len(c["findings"]) for c in bucket)
        title = f"{run_dir.name} — finding validation (validator {i})"
        sub = f"{run_dir.name} · {len(bucket)} skill · {nb_findings} finding assegnati"
        fname = f"validator_{i}.html"
        (out_dir / fname).write_text(
            render_page(bucket, title=title, subtitle=sub, run_key=f"{run_key}_validator{i}"),
            encoding="utf-8")
        written.append(fname)

    return {"out_dir": str(out_dir), "n_cases": len(cases), "n_findings": n_findings,
            "files": written, "per_validator": [len(b) for b in buckets]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path, help="cartella results/<run_id>")
    ap.add_argument("--engine", default="blue")
    ap.add_argument("--out", type=Path, help="default: <run>/validation")
    ap.add_argument("--n-validators", type=int, default=4)
    ap.add_argument("--coverage", type=int, default=None, help="default: n_validators - 1")
    ap.add_argument("--run-key", default=None)
    args = ap.parse_args()

    out = args.out or (args.run / "validation")
    res = generate(args.run, out, engine=args.engine, n_validators=args.n_validators,
                   coverage=args.coverage, run_key=args.run_key)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
