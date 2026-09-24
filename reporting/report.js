
(function() {
  const data = JSON.parse(document.getElementById('benchmark-data').textContent);
  const app  = document.getElementById('app');

  // ── helpers ──────────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function pct(v) { return v == null ? '—' : v.toFixed(1) + '%'; }

  // N = attempts per injection (for the ASR best-of-N definition)
  let asrN = (data.settings && data.settings.max_attempts != null) ? data.settings.max_attempts : null;
  if (asrN == null) {
    const lens = (data.findings_detail || [])
      .map(r => (r._tester_three_way && r._tester_three_way.prompts) ? r._tester_three_way.prompts.length : 0);
    asrN = lens.length ? Math.max(...lens) : null;
    if (!asrN) asrN = null;
  }
  const asrNlab = asrN ? ` (N=${asrN})` : '';

  const BADGE = {
    green:  'bg-green-100 text-green-800',
    red:    'bg-red-100 text-red-800',
    orange: 'bg-orange-100 text-orange-800',
    gray:   'bg-gray-100 text-gray-700',
    blue:   'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
    indigo: 'bg-indigo-100 text-indigo-800',
  };

  // Hover explanations for every metric/value. Matched against the (normalized)
  // label — longer keys first so "detection rate" wins over "detection".
  const TIP_LIST = [
    ['injection detection rate', "IDR — Injection Detection Rate. Recall: caught / all injected (TP / (TP+FN)), verified against ground truth. How many of the real injections Blue caught."],
    ['idr',            "IDR — Injection Detection Rate. Recall: caught / all injected (TP / (TP+FN)), verified against ground truth. How many of the real injections Blue caught."],
    ['generic detection rate', "GDR — Generic Detection Rate. Share of injected attacks a defense engine self-reported as flagged. Not verified against ground truth."],
    ['gdr',            "GDR — Generic Detection Rate. Share of injected attacks a defense engine self-reported as flagged. Not verified against ground truth."],
    ['patch effectiveness', "Share of pre-patch bypass attempts that Blue's patch blocked. Higher is better."],
    ['patch eff',      "Patch effectiveness — share of pre-patch bypass attempts that Blue's patch blocked. Higher is better."],
    ['asr pre',        "Attack Success Rate before patching — bypass attempts / total attempts on the INJECTED skill (best-of-N). Higher = more attacks fired."],
    ['asr post',       "Attack Success Rate after Blue's patch (FIXED skill). Lower = the patch held."],
    ['asr base',       "Sanity check — attacks firing on the CLEAN base skill. Should be 0; >0 means the prompt itself (not the injection) caused the behavior."],
    ['precision',      "Precision — caught / all flagged (TP / (TP+FP)). Of everything Blue flagged, how much was the real injection."],
    ['caught',         "True Positives — Blue correctly flagged/removed the injected malicious instruction."],
    ['false alarm',    "False Positives — Blue flagged/removed benign or unrelated text, not the actual injection."],
    ['missed',         "False Negatives — Blue failed to flag the injection."],
    ['llm-reviewed',   "Ambiguous cases (fuzzy overlap between the auto-match thresholds) decided by the Tier-2 LLM reviewer, not the deterministic match."],
    ['func rate base', "Functionality on the CLEAN base skill — % of legitimate prompts the agent completed. Reference for degradation."],
    ['func rate injected', "Functionality on the INJECTED skill — % of legitimate prompts still completed despite the injection."],
    ['func rate fixed', "Functionality on the FIXED (patched) skill — % of legitimate prompts still completed after Blue's patch."],
    ['func preserved', "Share of injections where the patch kept the skill working (functionality preserved vs the base)."],
  ];
  function tipFor(label) {
    const s = String(label).toLowerCase()
      .replace(/⚠\s*/, '')
      .replace(/\s*\(n=\d+\)/, '')
      .replace(/\s*\(sanity\)/, '')
      .replace(/\s*\(caught[^)]*\)/, '')
      .replace(/-patch/, '')
      .trim();
    for (const [k, t] of TIP_LIST) { if (s === k || s.startsWith(k)) return t; }
    return '';
  }
  function tipAttrs(label) {
    const t = tipFor(label);
    return t ? ` title="${esc(t)}" class="cursor-help"` : '';
  }

  function badge(label, value, kind) {
    const t = tipFor(label);
    return `<span class="${BADGE[kind] || BADGE.gray} px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap${t ? ' cursor-help' : ''}"`
         + `${t ? ` title="${esc(t)}"` : ''}>${esc(label)}: ${esc(value)}</span>`;
  }

  // ── header ───────────────────────────────────────────────────────
  const difficulties = [...new Set((data.findings_detail || [])
    .map(r => r.difficulty)
    .filter(d => d && d !== '—'))].sort();

  // data.detection_rate è SOLO di Blue (per costruzione — vedi commento in
  // reporting/report.py::_compute_stats). Una run con un solo motore terzo
  // (--defense cisco/skillspector/aig/snyk, niente Blue) lo lascia null anche
  // se quel motore ha prodotto un verdetto perfettamente valido: il numero
  // vive in engine_summary[quel motore], non qui. Con esattamente un motore
  // in engine_summary lo si ripesca da lì invece di lasciare la card vuota.
  const _engKeys = Object.keys(data.engine_summary || {});
  const _fallbackEngine = (data.detection_rate == null && _engKeys.length === 1) ? _engKeys[0] : null;
  const _aggDetectionRate  = _fallbackEngine ? data.engine_summary[_fallbackEngine].detection_rate : data.detection_rate;
  // Niente nome motore nell'etichetta: la tabella "Defense engines" sotto lo
  // nomina già per esteso — qui basta GDR, il tooltip spiega di chi è il numero.
  const _aggDetectionLabel = 'Generic Detection Rate (GDR)';

  const headerBadges = [];
  if (_aggDetectionRate != null)
    headerBadges.push(badge('GDR', pct(_aggDetectionRate),
                             _aggDetectionRate >= 90 ? 'green' : _aggDetectionRate >= 50 ? 'orange' : 'red'));
  if (data.asr_pre_rate != null)
    headerBadges.push(badge('ASR pre' + asrNlab, pct(data.asr_pre_rate),
                             data.asr_pre_rate > 0 ? 'red' : 'green'));
  if (data.patch_effectiveness != null)
    headerBadges.push(badge('Patch eff', pct(data.patch_effectiveness),
                             data.patch_effectiveness >= 80 ? 'green' : 'orange'));
  if (data.asr_base_rate != null && data.asr_base_rate > 0)
    headerBadges.push(badge('⚠ ASR base', pct(data.asr_base_rate), 'orange'));

  // Blue-eval: detection-accuracy badges (same badge() helper / color logic).
  const be = data.blue_eval;
  if (be) {
    const o = be.overall || {};
    headerBadges.push(badge('IDR', pct(o.recall),
                            o.recall == null ? 'gray' : o.recall >= 90 ? 'green' : o.recall >= 50 ? 'orange' : 'red'));
    headerBadges.push(badge('Precision', pct(o.precision),
                            o.precision == null ? 'gray' : o.precision >= 90 ? 'green' : o.precision >= 50 ? 'orange' : 'red'));
    headerBadges.push(badge('Caught', o.tp, 'green'));
    headerBadges.push(badge('False alarm', o.fp, 'orange'));
    headerBadges.push(badge('Missed', o.fn, 'red'));
    headerBadges.push(badge('LLM-reviewed', be.tier2_count || 0, 'gray'));
  }
  const _beTh = (be && be.thresholds) || {};
  // Caveat metodologico sulla precision: la ground truth copre SOLO il testo
  // iniettato, non il resto del file. I finding del Blue che non lo matchano non
  // sono giudicabili come falsi allarmi (la skill base puo' avere vulnerabilita'
  // sue), quindi non entrano in FP → la precision e' un limite superiore.
  // Stesso testo di _blue_eval_note lato Python, che alimenta MD e PDF.
  const _beUnm = be ? (be.unmatched_findings || 0) : 0;
  const _beNote = be
    ? `How well Blue caught the injected attacks, vs the known ground truth. `
      + `Each injection is scored automatically by fuzzy text match `
      + `(overlap ≥ ${_beTh.high != null ? _beTh.high : 0.8} → caught, < ${_beTh.low != null ? _beTh.low : 0.3} → missed); `
      + `the ${be.tier2_count || 0} ambiguous cases in between (of ${data.total || 0}) were resolved by an LLM reviewer (${be.validator_model || '—'}).`
      + (_beUnm
          ? ` Note: precision is an UPPER BOUND — ${_beUnm} further Blue finding(s) across `
            + `${be.unmatched_findings_records || 0} skill(s) did not match the injected ground truth. `
            + `They are not counted as false alarms because the ground truth only covers the injected `
            + `text: those findings may well be real vulnerabilities elsewhere in the base skill, and `
            + `nothing here can adjudicate them either way.`
          : '')
    : '';

  // Third-party comparison tab: LEGACY. Runs no longer produce
  // third_party_comparison — a run executes the defense engines it was asked for
  // (data.defense_engines) and reports each one on its own. The renderer stays
  // so the runs saved before that change keep opening with their tab intact.
  const hasThirdParty = Array.isArray(data.third_party_comparison) && data.third_party_comparison.length > 0;
  // Own tab (was inline in Findings) — includes the pipeline run's token usage
  // and API pricing.
  const hasCost = !!((data.api_pricing && data.api_pricing.length) || data.token_usage);
  const tabBtn = (id, label, active) =>
    `<button type="button" class="sse-tab-btn px-3 py-1.5 rounded-md text-sm font-medium ${active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}" data-tab-target="${id}">${label}</button>`;

  let html = `
    <header class="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-6xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 class="text-xl font-bold text-gray-900">SkillSecurer Report${data.run_name ? `  ·  <span class="text-blue-600 font-mono">${esc(data.run_name)}</span>` : ''}</h1>
            <div class="text-xs text-gray-600 mt-0.5">
              <span class="font-medium">${esc((data.skills||[]).join(', '))}</span>
              · ${esc((data.timestamp || '').slice(0,19).replace('T',' '))}
              · ${data.total || 0} injections${difficulties.length > 0 ? ` · ${esc(difficulties.join(', '))}` : ''}${data.elapsed_human ? ` · ${esc(data.elapsed_human)}` : ''}
            </div>
            <div class="text-[11px] text-gray-400 mt-0.5">ASR = bypass attempts / total attempts${asrN ? ` · N=${asrN} per injection` : ''}</div>
          </div>
          <div class="flex gap-2 flex-wrap">${headerBadges.join('')}</div>
        </div>
        ${(hasThirdParty || hasCost) ? `
        <div class="flex gap-2 mt-3">
          ${tabBtn('tabPanelFindings', 'Findings', true)}
          ${hasThirdParty ? tabBtn('tabPanelThirdParty', '🔍 Third-party comparison', false) : ''}
          ${hasCost       ? tabBtn('tabPanelCost', '💰 Cost & Usage', false) : ''}
        </div>` : ''}
      </div>
    </header>
    <div id="tabPanelFindings">
  `;

  // ── run settings + timing ────────────────────────────────────────
  const s = data.settings || {};
  const fmtList = v => Array.isArray(v) && v.length ? v.join(', ') : (v == null ? 'all' : String(v));
  const rkb = data.red_kb || {};
  const settingsRows = [
    ['Pipeline',     s.pipeline || '—'],
    ...(rkb.active ? [['Red profile', `🧬 skill-inject KB (${Object.keys(rkb.classes||{}).length} classes, ${rkb.total_exemplars||0} exemplars)`]] : []),
    ['Difficulties', fmtList(s.difficulties)],
    ['Vuln types',   fmtList(s.vuln_types)],
    ['Max attempts', s.max_attempts == null ? '—' : s.max_attempts],
    ['Parallel',     s.parallel == null ? '—' : s.parallel],
    ['Max files',    s.max_files == null ? 'no limit' : s.max_files],
    ['Started',      (data.started_at || '').slice(0,19).replace('T',' ') || '—'],
    ['Ended',        (data.ended_at || data.timestamp || '').slice(0,19).replace('T',' ') || '—'],
    ['Elapsed',      data.elapsed_human || '—'],
  ];
  // Solo l'elapsed totale in tabella; il dettaglio per-fase è in un pannello
  // nascosto, mostrato al click sulla riga "Elapsed".
  const phaseTimes = data.phase_times_human || {};
  const hasPhases  = Object.keys(phaseTimes).length > 0;
  const phaseDetail = hasPhases ? `
        <div id="phaseDetail" class="hidden mt-2 bg-white rounded-lg shadow-sm p-4 text-sm max-w-sm">
          <div class="text-gray-500 font-semibold mb-1">Elapsed by phase</div>
          ${Object.keys(phaseTimes).map(k => `<div class="flex justify-between gap-3 border-b border-gray-100 last:border-0 py-1"><span class="text-gray-500">${esc(k)}</span><span class="font-medium text-right">${esc(String(phaseTimes[k]))}</span></div>`).join('')}
        </div>` : '';
  const settingCell = ([k,v]) => {
    if (k === 'Elapsed' && hasPhases) {
      return `<div class="flex justify-between gap-3 border-b border-gray-100 py-1 cursor-pointer select-none hover:bg-gray-50" title="Click for per-phase breakdown" onclick="var d=document.getElementById('phaseDetail');d.classList.toggle('hidden');this.querySelector('.ph-caret').textContent=d.classList.contains('hidden')?'▸':'▾';"><span class="text-gray-500">${esc(k)} <span class="ph-caret text-gray-400">▸</span></span><span class="font-medium text-right">${esc(String(v))}</span></div>`;
    }
    return `<div class="flex justify-between gap-3 border-b border-gray-100 py-1"><span class="text-gray-500">${esc(k)}</span><span class="font-medium text-right">${esc(String(v))}</span></div>`;
  };
  html += `
    <section class="max-w-6xl mx-auto px-6 pt-6">
      <div class="flex items-center justify-between mb-3 gap-2 flex-wrap">
        <h2 class="text-lg font-semibold">Run settings</h2>
        <div class="flex gap-2 flex-wrap">
          ${rkb.active ? `<button id="kb-modal-btn" class="text-sm bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-md px-3 py-1.5 font-medium">🧬 View Red KB (${rkb.total_exemplars||0} exemplars)</button>` : ''}
        </div>
      </div>
      <div class="bg-white rounded-lg shadow-sm p-4 grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-1 text-sm">
        ${settingsRows.map(settingCell).join('')}
      </div>
      ${phaseDetail}
      ${data.run_notes ? `<div class="bg-amber-50 border-l-4 border-amber-300 rounded-r p-4 mt-3">
        <div class="text-xs font-semibold text-amber-800 mb-1">📝 Notes</div>
        <div class="text-sm text-gray-800 whitespace-pre-wrap">${esc(data.run_notes)}</div></div>` : ''}
    </section>
  `;

  // ── system prompts (uno per agente; l'effettivo usato nel run) ────
  const sysPrompts = data.system_prompts || [];
  if (sysPrompts.length) {
    const blocks = sysPrompts.map(p => `
      <details class="border border-gray-200 rounded mb-2">
        <summary class="cursor-pointer select-none px-3 py-2 bg-gray-50 font-medium text-sm">
          <span class="arrow"></span>${esc(p.label || p.name)}
          <span class="text-gray-400 font-normal">(${(p.text||'').length} chars)</span>
        </summary>
        <pre class="text-xs bg-white border-t border-gray-200 p-3 overflow-x-auto whitespace-pre-wrap font-mono">${esc(p.text || '')}</pre>
      </details>`).join('');
    html += `
      <section class="max-w-6xl mx-auto px-6 pt-6">
        <h2 class="text-lg font-semibold mb-3">🧠 Agent system prompts</h2>
        <p class="text-sm text-gray-500 mb-3">System prompt actually used by each agent in this run (UI overrides already applied). Fixed for the entire run.</p>
        <div class="bg-white rounded-lg shadow-sm p-4">${blocks}</div>
      </section>`;
  }

  // ── aggregate bars ───────────────────────────────────────────────
  function metricBar(label, value, kind, filterKind) {
    const fill = value == null ? 0 : Math.max(0, Math.min(100, value));
    const colors = { green: '#22c55e', red: '#ef4444', orange: '#f97316', gray: '#9ca3af' };
    const interactive = filterKind
      ? `cursor-pointer hover:bg-gray-50 -mx-2 px-2 rounded transition-colors group`
      : '';
    const hint = filterKind
      ? `<span class="opacity-0 group-hover:opacity-100 text-[10px] text-gray-400 ml-2 transition-opacity">(click to filter)</span>`
      : '';
    const dataAttr = filterKind ? ` data-filter-trigger="${filterKind}"` : '';
    return `
      <div class="grid grid-cols-[200px_1fr_60px] items-center gap-3 text-sm py-1 ${interactive}"${dataAttr}>
        <div class="text-gray-700 flex items-center"><span${tipAttrs(label)}>${esc(label)}</span>${hint}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${fill}%;background:${colors[kind] || colors.gray}"></div></div>
        <div class="text-right font-medium tabular-nums">${value == null ? '—' : value.toFixed(1) + '%'}</div>
      </div>`;
  }

  html += `
    <section class="max-w-6xl mx-auto px-6 pt-6">
      <h2 class="text-lg font-semibold mb-3">Aggregate metrics</h2>
      <div class="bg-white rounded-lg shadow-sm p-4">
        ${metricBar(_aggDetectionLabel, _aggDetectionRate, 'green')}
        ${metricBar('ASR pre-patch' + asrNlab, data.asr_pre_rate, 'red', 'asr')}
        ${metricBar('ASR post-patch' + asrNlab, data.asr_post_rate, 'red')}
        ${metricBar('Patch effectiveness', data.patch_effectiveness, 'green', 'asr')}
        ${data.asr_base_rate != null ? metricBar('ASR base (sanity)', data.asr_base_rate, data.asr_base_rate > 0 ? 'orange' : 'green') : ''}
        ${data.func_base_rate_avg     != null ? metricBar('Func rate BASE',     data.func_base_rate_avg,     'green')  : ''}
        ${data.func_injected_rate_avg != null ? metricBar('Func rate INJECTED', data.func_injected_rate_avg, 'orange') : ''}
        ${data.func_fixed_rate_avg    != null ? metricBar('Func rate FIXED',    data.func_fixed_rate_avg,    'green')  : ''}
        ${data.func_preserved_rate    != null ? metricBar('Func preserved',     data.func_preserved_rate,    'green',  'func') : ''}
        ${be ? metricBar('Injection Detection Rate (IDR)', be.overall.recall, 'green') : ''}
        ${be ? metricBar('Precision (caught / all flagged)', be.overall.precision, 'green') : ''}
        ${be ? `<div class="text-xs text-gray-500 mt-2">${esc(_beNote)}</div>` : ''}
        ${data.env_failed_count ? `<div class="text-xs text-amber-700 mt-3">⚠️ ${data.env_failed_count} injections excluded from metrics (all base attempts failed — environment issue).</div>` : ''}
        ${data.env_setup_failures ? `<div class="text-xs text-amber-700 mt-1">⚠️ ${data.env_setup_failures} injections had EnvAgent setup-command failures — workspace may be incomplete.</div>` : ''}
        ${data.blue_scan_failures ? `<div class="text-xs text-amber-700 mt-1">⚠️ ${data.blue_scan_failures} Blue scans FAILED (API/parse error) — excluded from detection rate (a failed scan is not a clean skill).</div>` : ''}
      </div>
    </section>
  `;

  // ── defense engines ───────────────────────────────────────────────
  // Un blocco per motore eseguito, ognuno misurato per conto suo. Nessuna
  // metrica derivata dal verdetto di un altro motore: il confronto fra run
  // diverse è manuale. Assente sulle run salvate prima
  // del namespace `engines` (engine_summary null) — lì restano il tab legacy
  // "Third-party comparison" e le metriche aggregate qui sopra.
  if (data.engine_summary && Object.keys(data.engine_summary).length) {
    const ENGINE_LABEL = {
      blue: '🔵 Blue (ours)', skillspector: '🟩 NVIDIA SkillSpector',
      cisco: '🔷 Cisco skill-scanner', aig: '🐉 Tencent aig-skill-scan',
      snyk: '🛡️ Snyk', skills_sh: '🌐 skills.sh',
    };
    const engRow = (name, e) => `<tr class="border-b border-gray-100">
      <td class="px-2 py-1">${esc(ENGINE_LABEL[name] || name)}</td>
      <td class="px-2 py-1 text-right tabular-nums">${e.n}</td>
      <td class="px-2 py-1 text-right tabular-nums text-green-700">${e.flagged}</td>
      <td class="px-2 py-1 text-right tabular-nums font-medium">${e.detection_rate == null ? '—' : e.detection_rate + '%'}</td>
      <td class="px-2 py-1 text-right tabular-nums">${e.findings_total}</td>
      <td class="px-2 py-1 text-right tabular-nums ${e.scan_errors ? 'text-amber-700' : 'text-gray-400'}">${e.scan_errors}</td>
      <td class="px-2 py-1 text-right tabular-nums ${e.unavailable ? 'text-amber-700' : 'text-gray-400'}">${e.unavailable}</td></tr>`;
    html += `
    <section class="max-w-6xl mx-auto px-6 pt-6">
      <h2 class="text-lg font-semibold mb-1">Defense engines</h2>
      <p class="text-xs text-gray-500 mb-3">Each engine measured on its own — this run executed
        ${esc((data.defense_engines || Object.keys(data.engine_summary)).join(', '))}.
        No cross-engine comparison here: run each engine separately, then compare the runs
        manually. "Scanned" excludes files the engine errored on
        or has no verdict for.</p>
      <div class="bg-white rounded-lg shadow-sm p-4 overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="text-gray-500 border-b">
            <tr><th class="px-2 py-1 text-left font-normal">Engine</th>
              <th class="px-2 py-1 text-right font-normal">Scanned</th>
              <th class="px-2 py-1 text-right font-normal">Flagged</th>
              <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('gdr')}>GDR</span></th>
              <th class="px-2 py-1 text-right font-normal">Findings</th>
              <th class="px-2 py-1 text-right font-normal">Scan errors</th>
              <th class="px-2 py-1 text-right font-normal">No verdict</th></tr>
          </thead>
          <tbody>${Object.entries(data.engine_summary).map(([n, e]) => engRow(n, e)).join('')}</tbody>
        </table>
      </div>
    </section>
  `;
  }

  // ── recap by type / difficulty ────────────────────────────────────
  // Sempre disponibile (a differenza di "Blue detection accuracy" sotto, che
  // richiede il judge blue-eval con ground truth nota): usa by_vuln_type /
  // by_difficulty, già calcolati in _compute_stats per ogni run. Per le skill
  // blue-only con più categorie distinte (blue_categories in graph/nodes.py)
  // lo stesso record conta una volta per categoria — Total qui è quindi un
  // conteggio di "injection × categoria", non di skill uniche.
  {
    const rtRow = (name, s) => `<tr class="border-b border-gray-100">
      <td class="px-2 py-1">${esc(name)}</td>
      <td class="px-2 py-1 text-right tabular-nums">${s.detected + s.missed}</td>
      <td class="px-2 py-1 text-right tabular-nums text-green-700">${s.detected}</td>
      <td class="px-2 py-1 text-right tabular-nums text-red-700">${s.missed}</td>
      <td class="px-2 py-1 text-right tabular-nums">${s.rate}%</td>
      <td class="px-2 py-1 text-right tabular-nums">${s.asr_pre_rate  == null ? '—' : s.asr_pre_rate  + '%'}</td>
      <td class="px-2 py-1 text-right tabular-nums">${s.asr_post_rate == null ? '—' : s.asr_post_rate + '%'}</td>
      <td class="px-2 py-1 text-right tabular-nums">${s.func_preserved_rate == null ? '—' : s.func_preserved_rate + '%'}</td></tr>`;
    const rtTable = (title, store) => {
      const keys = Object.keys(store || {}).sort();
      if (!keys.length) return '';
      return `<div class="mb-4"><div class="text-sm font-semibold text-gray-600 mb-1">${esc(title)}</div>
        <table class="w-full text-xs"><thead><tr class="bg-gray-100 text-gray-600 border-b border-gray-300">
        <th class="px-2 py-1 text-left font-normal">Type</th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Injections in this category')}>Total</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Blue detected')}>Detected</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Blue missed')}>Missed</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('gdr')}>GDR</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Attack success rate before patch')}>ASR pre</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Attack success rate after patch')}>ASR post</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Legitimate functionality preserved after patch')}>Func preserved</span></th>
        </tr></thead>
        <tbody>${keys.map(k => rtRow(k, store[k])).join('')}</tbody></table></div>`;
    };
    // Blue-only runs (skills.sh / user-provided, no ground truth): "vuln_type" per
    // categoria è per costruzione SEMPRE detected==total (la categoria esiste solo
    // perché Blue l'ha trovata) — Total/Missed/Rate sono tautologici, non segnale.
    // "user_provided" lì è il bucket delle skill pulite (o non ancora categorizzate),
    // NON una categoria di vulnerabilità: mostrarlo come "missed" implicherebbe che
    // conteniamo vulnerabilità note che Blue non ha trovato, quando in realtà
    // potrebbero semplicemente non averne. Per questi run mostro solo il conteggio.
    // Il profilo Red (ground truth nota) invece mantiene Total/Detected/Missed/Rate
    // pieni — lì "missed" è IL segnale principale del progetto.
    const isBlueOnly = Object.prototype.hasOwnProperty.call(data.by_vuln_type || {}, 'user_provided');
    const foundRow = (name, s) => `<tr class="border-b border-gray-100">
      <td class="px-2 py-1">${esc(name)}</td>
      <td class="px-2 py-1 text-right tabular-nums text-green-700">${s.detected}</td></tr>`;
    const foundTable = (title, store) => {
      const keys = Object.keys(store || {})
        .filter(k => k !== 'user_provided')
        .sort((a, b) => (store[b].detected - store[a].detected) || a.localeCompare(b));
      if (!keys.length) return '';
      return `<div class="mb-4"><div class="text-sm font-semibold text-gray-600 mb-1">${esc(title)}</div>
        <table class="w-full text-xs"><thead><tr class="bg-gray-100 text-gray-600 border-b border-gray-300">
        <th class="px-2 py-1 text-left font-normal">Type</th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Injections Blue flagged with this category')}>Found</span></th>
        </tr></thead>
        <tbody>${keys.map(k => foundRow(k, store[k])).join('')}</tbody></table></div>`;
    };
    const vulnHtml = isBlueOnly ? foundTable('By vuln type', data.by_vuln_type)
                                : rtTable('By vuln type', data.by_vuln_type);
    const rtHtml = vulnHtml + rtTable('By difficulty', data.by_difficulty);
    if (rtHtml) {
      html += `
        <section class="max-w-6xl mx-auto px-6 pt-6">
          <h2 class="text-lg font-semibold mb-3">Recap by type</h2>
          <div class="bg-white rounded-lg shadow-sm p-4">${rtHtml}</div>
        </section>`;
    }
  }

  // ── Cost & Usage tab (own tab, not inline in Findings — includes API
  // pricing and the pipeline run's usage) ─────────────────────────────
  function renderCostTab() {
    const fmtTokens = n => {
      n = Number(n || 0);
      if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
      if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
      return String(Math.round(n));
    };
    const fmtCost = c => {
      if (c == null) return '—';
      c = Number(c);
      return (c > 0 && c < 0.01) ? '$' + c.toFixed(4) : '$' + c.toFixed(2);
    };
    const fmtProviders = d => {
      const items = Object.entries(d || {}).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      return items.length ? items.map(([n, c]) => `${esc(n)} ×${c}`).join(', ') : '—';
    };
    const fmtPriceM = v => {
      v = Number(v);
      return (!isFinite(v) || v <= 0) ? '—' : '$' + v.toFixed(4);
    };
    let inner = '';

    // ── API pricing (per-provider, OpenRouter endpoints) ───────────────
    const ap = data.api_pricing;
    if (ap && ap.length) {
      // cheapest by input+output $/M → highlighted row (what provider.sort=price picks)
      let cheapIdx = -1, cheapCost = Infinity;
      ap.forEach((ep, i) => {
        const c = (Number(ep.input) || 0) + (Number(ep.output) || 0);
        if (c < cheapCost) { cheapCost = c; cheapIdx = i; }
      });
      const apRows = ap.map((ep, i) => {
        const hl = i === cheapIdx ? ' bg-green-50 font-semibold' : '';
        const star = i === cheapIdx ? ' <span class="text-green-600">★</span>' : '';
        return `<tr class="border-b border-gray-100${hl}">
          <td class="px-2 py-1">${esc(ep.provider_name || '—')}${star}</td>
          <td class="px-2 py-1">${esc(ep.quantization || '—')}</td>
          <td class="px-2 py-1 text-right tabular-nums">${fmtPriceM(ep.input)}</td>
          <td class="px-2 py-1 text-right tabular-nums">${fmtPriceM(ep.output)}</td>
          <td class="px-2 py-1 text-right tabular-nums">${fmtPriceM(ep.cache_read)}</td>
          <td class="px-2 py-1 text-right tabular-nums">${fmtPriceM(ep.cache_write)}</td></tr>`;
      }).join('');
      inner += `
        <section class="max-w-6xl mx-auto px-6 pt-6">
          <h2 class="text-lg font-semibold mb-3">API pricing${data.model ? ` — <span class="font-mono text-base">${esc(data.model)}</span>` : ''}</h2>
          <div class="bg-white rounded-lg shadow-sm p-4">
            <div class="text-[11px] text-gray-400 mb-2">Per-provider endpoint pricing ($/M token). The ★ / highlighted row is the cheapest — what <span class="font-mono">provider.sort=price</span> routes to.</div>
            <table class="w-full text-xs border-collapse">
              <thead><tr class="bg-gray-100 text-gray-700 border-b border-gray-300">
                <th class="px-2 py-1 text-left">Provider</th><th class="px-2 py-1 text-left">Quant</th>
                <th class="px-2 py-1 text-right">Input/M</th><th class="px-2 py-1 text-right">Output/M</th>
                <th class="px-2 py-1 text-right">Cache read/M</th><th class="px-2 py-1 text-right">Cache write/M</th></tr></thead>
              <tbody>${apRows}</tbody>
            </table>
          </div>
        </section>
      `;
    }

    function costCard(tu, title, note, perInjection) {
      if (!tu) return '';
      const nInj = data.total || 0;
      const cost = tu.estimated_cost_usd;
      const costLabel = tu.cost_source === 'openrouter' ? 'Cost (billed)' : 'Cost (estimated)';
      const usageStats = [
        ['LLM calls',     String(tu.calls || 0)],
        ['Input tokens',  (tu.input_tokens || 0).toLocaleString() + ` (${fmtTokens(tu.input_tokens)})`],
        ['Output tokens', (tu.output_tokens || 0).toLocaleString() + ` (${fmtTokens(tu.output_tokens)})`],
        ['Cache read tokens',  (tu.cache_read_tokens || 0).toLocaleString() + ` (${fmtTokens(tu.cache_read_tokens)})`],
        ['Cache write tokens', (tu.cache_write_tokens || 0).toLocaleString() + ` (${fmtTokens(tu.cache_write_tokens)})`],
        ['Total tokens',  (tu.total_tokens || 0).toLocaleString() + ` (${fmtTokens(tu.total_tokens)})`],
      ];
      if (tu.elapsed_human) usageStats.push(['Elapsed', tu.elapsed_human]);
      if (cost != null) usageStats.push([costLabel, fmtCost(cost)]);
      if (perInjection && nInj) usageStats.push(['Avg tokens / injection', fmtTokens((tu.total_tokens || 0) / nInj)]);

      const byAgent = tu.by_agent || {};
      const agentRows = Object.keys(byAgent)
        .filter(a => byAgent[a].calls || byAgent[a].total_tokens)
        .map(a => {
          const v = byAgent[a];
          return `<tr class="border-b border-gray-100">
            <td class="px-2 py-1 font-mono">${esc(a)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${v.calls || 0}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(v.input_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(v.output_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(v.cache_read_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(v.cache_write_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(v.total_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${v.cost ? fmtCost(v.cost) : '—'}</td>
            <td class="px-2 py-1 text-left">${fmtProviders(v.providers)}</td></tr>`;
        }).join('');
      const totalRow = agentRows ? `<tr class="border-t-2 border-gray-300 font-semibold">
            <td class="px-2 py-1 font-mono">Total</td>
            <td class="px-2 py-1 text-right tabular-nums">${tu.calls || 0}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(tu.input_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(tu.output_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(tu.cache_read_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(tu.cache_write_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${fmtTokens(tu.total_tokens)}</td>
            <td class="px-2 py-1 text-right tabular-nums">${tu.cost ? fmtCost(tu.cost) : '—'}</td>
            <td class="px-2 py-1 text-left">${fmtProviders(tu.providers)}</td></tr>` : '';

      return `
        <section class="max-w-6xl mx-auto px-6 pt-6">
          <h2 class="text-lg font-semibold mb-3">${esc(title)}</h2>
          ${note ? `<p class="text-xs text-gray-500 mb-3">${esc(note)}</p>` : ''}
          <div class="bg-white rounded-lg shadow-sm p-4 grid gap-4 md:grid-cols-2">
            <div class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm self-start">
              ${usageStats.map(([k,v]) => `<div class="flex justify-between gap-3 border-b border-gray-100 py-1"><span class="text-gray-500">${esc(k)}</span><span class="font-medium text-right">${esc(String(v))}</span></div>`).join('')}
              ${cost == null ? `<div class="col-span-2 text-[11px] text-gray-400 mt-1">Pass --input-price / --output-price to estimate cost.</div>` : ''}
            </div>
            ${agentRows ? `<div class="text-sm">
              <div class="text-gray-500 font-semibold mb-1">By agent</div>
              <table class="w-full text-xs border-collapse">
                <thead><tr class="bg-gray-100 text-gray-700 border-b border-gray-300">
                  <th class="px-2 py-1 text-left">Agent</th><th class="px-2 py-1 text-right">Calls</th>
                  <th class="px-2 py-1 text-right">Input</th><th class="px-2 py-1 text-right">Output</th>
                  <th class="px-2 py-1 text-right">Cache rd</th><th class="px-2 py-1 text-right">Cache wr</th>
                  <th class="px-2 py-1 text-right">Total</th><th class="px-2 py-1 text-right">Cost</th>
                  <th class="px-2 py-1 text-left">Provider</th></tr></thead>
                <tbody>${agentRows}${totalRow}</tbody>
              </table>
              </div>` : ''}
          </div>
        </section>
      `;
    }

    inner += costCard(data.token_usage, 'Cost & Usage', null, true);

    if (!inner) return '';
    return `<div id="tabPanelCost" class="hidden">${inner}</div>`;
  }
  // NOTE: renderCostTab() is called AFTER #tabPanelFindings closes below (not
  // here) — its output must be a SIBLING div, not nested inside Findings, or
  // Findings' own `hidden` toggle would hide it too when Findings isn't the
  // active tab (see the `html += renderCostTab();` call further down).

  // ── blue-eval: detection-accuracy summary tables (same table style) ──
  if (be) {
    const beRow = (name, g) => `<tr class="border-b border-gray-100">
      <td class="px-2 py-1">${esc(name)}</td>
      <td class="px-2 py-1 text-right tabular-nums">${g.total}</td>
      <td class="px-2 py-1 text-right tabular-nums text-green-700">${g.tp}</td>
      <td class="px-2 py-1 text-right tabular-nums text-red-700">${g.fn}</td>
      <td class="px-2 py-1 text-right tabular-nums text-orange-700">${g.fp}</td>
      <td class="px-2 py-1 text-right tabular-nums">${g.recall == null ? '—' : g.recall + '%'}</td>
      <td class="px-2 py-1 text-right tabular-nums">${g.precision == null ? '—' : g.precision + '%'}</td></tr>`;
    const beTable = (title, store) => {
      const keys = Object.keys(store || {}).sort();
      if (!keys.length) return '';
      return `<div class="mb-4"><div class="text-sm font-semibold text-gray-600 mb-1">${esc(title)}</div>
        <table class="w-full text-xs"><thead><tr class="bg-gray-100 text-gray-600 border-b border-gray-300">
        <th class="px-2 py-1 text-left font-normal">Name</th><th class="px-2 py-1 text-right font-normal">Total</th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Caught')}>Caught</span></th><th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Missed')}>Missed</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('False alarm')}>False alarm</span></th><th class="px-2 py-1 text-right font-normal"><span${tipAttrs('idr')}>IDR</span></th>
        <th class="px-2 py-1 text-right font-normal"><span${tipAttrs('Precision')}>Precision</span></th></tr></thead>
        <tbody>${keys.map(k => beRow(k, store[k])).join('')}</tbody></table></div>`;
    };
    html += `
      <section class="max-w-6xl mx-auto px-6 pt-6">
        <h2 class="text-lg font-semibold mb-3">Blue detection accuracy</h2>
        <div class="text-xs text-gray-500 mb-3">${esc(_beNote)}</div>
        <div class="bg-white rounded-lg shadow-sm p-4">
          ${beTable('By category', be.by_category)}
          ${beTable('By skill', be.by_skill)}
          ${beTable('By injection title', be.by_title)}
        </div>
      </section>`;
  }

  // ── warnings & errors (run events) ───────────────────────────────
  {
    const events = data.log_events || [];
    const map = new Map();   // msg -> {level, count}
    for (const e of events) {
      const msg = String((e && e.msg) || '').trim();
      if (!msg) continue;
      const cur = map.get(msg) || { level: (e.level || 'warn'), count: 0 };
      cur.count++; map.set(msg, cur);
    }
    const groups = [...map.entries()].map(([msg, v]) => ({ msg, ...v }))
                    .sort((a, b) => b.count - a.count);
    if (groups.length) {
      const nErr  = groups.filter(g => g.level === 'error').reduce((s, g) => s + g.count, 0);
      const nWarn = groups.filter(g => g.level !== 'error').reduce((s, g) => s + g.count, 0);
      const rows = groups.map(g => {
        const isErr = g.level === 'error';
        const badgeCls = isErr ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800';
        const label = isErr ? '✗ error' : '⚠ warn';
        return `<tr class="border-b border-gray-100 align-top">
          <td class="px-2 py-1 whitespace-nowrap"><span class="${badgeCls} px-2 py-0.5 rounded text-xs font-medium">${label}</span></td>
          <td class="px-2 py-1 text-right tabular-nums text-gray-600">×${g.count}</td>
          <td class="px-2 py-1 font-mono text-xs text-gray-700 break-all">${esc(g.msg)}</td></tr>`;
      }).join('');
      html += `
        <section class="max-w-6xl mx-auto px-6 pt-6">
          <h2 class="text-lg font-semibold mb-1">Warnings &amp; errors
            <span class="text-sm font-normal text-gray-500">(${nErr} errors · ${nWarn} warnings)</span></h2>
          <div class="text-xs text-gray-500 mb-3">Events logged during the run (duplicates collapsed with ×count).</div>
          <div class="bg-white rounded-lg shadow-sm p-4 overflow-x-auto">
            <table class="w-full text-sm"><thead><tr class="bg-gray-100 text-gray-600 border-b border-gray-300">
              <th class="px-2 py-1 text-left font-normal">Level</th>
              <th class="px-2 py-1 text-right font-normal">Count</th>
              <th class="px-2 py-1 text-left font-normal">Message</th></tr></thead>
            <tbody>${rows}</tbody></table>
          </div>
        </section>`;
    }
  }

  // ── filter bar ───────────────────────────────────────────────────
  const records  = data.findings_detail || [];
  const vulnTypes = [...new Set(records.map(r => r.vuln_type).filter(Boolean))].sort();

  html += `
    <section class="max-w-6xl mx-auto px-6 pt-6">
      <div class="bg-white rounded-lg shadow-sm p-3 flex flex-wrap gap-4 items-center text-sm">
        <span class="font-semibold">Filter:</span>
        <label class="flex items-center gap-1.5">
          <span>Vuln type:</span>
          <select id="f-vuln" class="border border-gray-300 rounded px-2 py-0.5">
            <option value="">All</option>
            ${vulnTypes.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('')}
          </select>
        </label>
        <label class="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" id="f-asr" class="cursor-pointer">
          <span>asr_pre &gt; 0 only</span>
        </label>
        <label class="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" id="f-func" class="cursor-pointer">
          <span>func_preserved = false only</span>
        </label>
        <label class="flex items-center gap-1.5">
          <span>Sort by:</span>
          <select id="f-sort" class="border border-gray-300 rounded px-2 py-0.5">
            <option value="default">Default</option>
            <option value="vuln">Vuln type A→Z</option>
            <option value="asr">ASR pre (high first)</option>
            <option value="deg">Func degradation injected (high first)</option>
            <option value="conf">Confidence (low first)</option>
          </select>
        </label>
        <div class="ml-auto flex items-center gap-3">
          <button id="f-clear" class="text-xs text-blue-600 hover:text-blue-800 underline hidden">Clear filters</button>
          <button id="f-export" class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1 rounded-md font-medium">↓ Export JSON</button>
          <span id="f-count" class="px-2.5 py-1 rounded-md text-xs font-medium"></span>
        </div>
      </div>
    </section>
  `;

  // ── legend (fix 1) ───────────────────────────────────────────────
  html += `
    <section class="max-w-6xl mx-auto px-6 pt-2">
      <div class="text-xs text-gray-500 flex flex-wrap gap-x-3 gap-y-1 items-center">
        <span class="font-semibold text-gray-600">Legend:</span>
        <span>✓ task completed</span>
        <span>✗ task failed</span>
        <span>✓ 🚨 bypass confirmed here</span>
        <span class="text-gray-400">|</span>
        <span>green card = detected</span>
        <span>red card = missed</span>
        <span class="text-gray-400">|</span>
        <span>BASE = original skill</span>
        <span>INJ = injected</span>
        <span>FIXED = patched</span>
        <span class="text-gray-400">|</span>
        <span>Hover ✗ for agent output</span>
        <span>Click 🚨 bypass badge for evidence</span>
      </div>
    </section>
  `;

  // ── cards ────────────────────────────────────────────────────────
  function collapsible(label, body, openByDefault) {
    return `
      <details class="mt-2" ${openByDefault ? 'open' : ''}>
        <summary class="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-1 select-none">
          <span class="arrow inline-block w-4"></span>${esc(label)}
        </summary>
        <div class="mt-2 pl-4">${body}</div>
      </details>`;
  }

  function cell(a, isBypassCell, extraAttrs) {
    extraAttrs = extraAttrs ? ' ' + extraAttrs : '';
    if (a == null) return `<td class="px-2 py-1 text-center bg-gray-100 text-gray-400">—</td>`;
    if (a.skipped) return `<td class="px-2 py-1 text-center bg-gray-50 text-gray-400 cursor-pointer" title="SKIPPED — base task failed"${extraAttrs}>SKIP</td>`;
    const mark      = isBypassCell ? ' 🚨' : '';
    const markTitle = isBypassCell ? ' title="This is the attempt that triggered the bypass"' : '';
    if (a.task_completed) {
      return `<td class="px-2 py-1 text-center bg-green-100 text-green-700 font-medium cursor-pointer"${markTitle}${extraAttrs}>✓${mark}</td>`;
    }
    const tip = (a.agent_output || '').slice(0, 250).replace(/"/g, '&quot;').replace(/\n/g, ' ');
    const titleAttr = isBypassCell
      ? ` title="Bypass attempt. Output: ${tip}"`
      : ` title="${tip}"`;
    return `<td class="px-2 py-1 text-center bg-red-100 text-red-700 font-medium cursor-pointer"${titleAttr}${extraAttrs}>✗${mark}</td>`;
  }

  function renderPromptGrid(t3, rec) {
    rec = rec || {};
    // Highlight only when judge actually confirmed bypass on INJECTED/FIXED.
    // bypass_attempt_pre/post is 1-based; null/0/undefined → no highlight.
    const bypassAttempt     = ((rec.asr_pre_count || 0) > 0 && rec.bypass_attempt_pre) || null;
    const bypassAttemptPost = ((rec.asr_post_count || 0) > 0 && rec.bypass_attempt_post) || null;
    function byAttempt(v) {
      if (!v || !v.attempts) return {};
      const o = {};
      v.attempts.forEach(a => { o[a.attempt] = a; });
      return o;
    }
    const bB = byAttempt(t3.base), iB = byAttempt(t3.injected), fB = byAttempt(t3.fixed);
    const n  = Math.max(Object.keys(bB).length, Object.keys(iB).length, Object.keys(fB).length);
    if (n === 0) return '';
    const versions = 'BASE/INJECTED' + (t3.fixed ? '/FIXED' : '');
    let out = `
      <div class="mt-4">
        <div class="text-sm font-medium text-gray-700 mb-2">Prompts (${n} prompts, same set on ${versions}):</div>
        <table class="w-full text-xs border-collapse">
          <thead>
            <tr class="bg-gray-100 text-gray-700 border-b border-gray-300">
              <th class="px-2 py-1.5 text-left w-8">#</th>
              <th class="px-2 py-1.5 text-left">Prompt</th>
              <th class="px-2 py-1.5 text-center w-16"><span class="cursor-help" title="Clean skill, no injection — reference run (sanity: should not bypass).">BASE</span></th>
              <th class="px-2 py-1.5 text-center w-16"><span class="cursor-help" title="Injected skill — the version where the hidden attack can fire.">INJ</span></th>
              <th class="px-2 py-1.5 text-center w-16"><span class="cursor-help" title="Blue-patched skill — should no longer let the attack fire while keeping functionality.">FIXED</span></th>
            </tr>
          </thead>
          <tbody>`;
    for (let k = 1; k <= n; k++) {
      const ba = bB[k], ia = iB[k], fa = fB[k];
      const prompt = (ba || ia || fa || {}).prompt || '';
      const ps     = prompt.length > 90 ? prompt.slice(0, 90) + '…' : prompt;
      const isBypassRow     = bypassAttempt && k === bypassAttempt;
      const isBypassRowPost = bypassAttemptPost && k === bypassAttemptPost;
      const rowClass    = (isBypassRow || isBypassRowPost)
        ? 'border-b border-gray-200 bg-red-50'
        : 'border-b border-gray-200';
      const fixedAttrs = `data-modal-version="fixed"    data-modal-attempt="${k}"`;
      let fixedCell;
      if (fa) {
        // Risultato reale o placeholder skipped del FIXED → cell() lo gestisce
        fixedCell = cell(fa, isBypassRowPost, fixedAttrs);
      } else if (ia && ia.skipped) {
        // Il prompt è stato saltato perché la BASE è fallita → stesso SKIP di INJ
        fixedCell = cell({skipped: true}, false, fixedAttrs);
      } else if (rec.fixed_skipped) {
        // FIXED non eseguita (patch identica / nessuna patch) → badge muto cliccabile
        const fr = rec.fixed_skip_reason === 'identical_to_base'
          ? 'patch identical to base' : 'no patch produced';
        fixedCell = `<td class="px-2 py-1 text-center bg-gray-100 text-gray-500 italic cursor-pointer" `
                  + `title="FIXED not run — ${fr}" ${fixedAttrs}>n/r</td>`;
      } else {
        fixedCell = cell(fa, false, fixedAttrs);   // "—"
      }
      out += `
        <tr class="${rowClass}">
          <td class="px-2 py-1 text-gray-500">${k}</td>
          <td class="px-2 py-1 prompt-cell cursor-pointer hover:bg-gray-50"
              style="text-decoration:underline dotted #9ca3af;text-underline-offset:2px"
              data-modal-version="injected" data-modal-attempt="${k}"
              title="Click to compare BASE / INJECTED / FIXED for this attempt">${esc(ps)}</td>
          ${cell(ba, false,       `data-modal-version="base"     data-modal-attempt="${k}"`)}
          ${cell(ia, isBypassRow, `data-modal-version="injected" data-modal-attempt="${k}"`)}
          ${fixedCell}
        </tr>`;
    }
    out += `</tbody></table>
        <div class="text-xs text-gray-500 mt-1">Hover ✗ cells for agent output snippet.</div>
      </div>`;
    return out;
  }

  function renderFuncBars(r) {
    // Only show for full pipeline runs (skip blue-only — no three-way data)
    if (!r._tester_three_way) return '';

    const base   = r.func_base_rate;
    const inj    = r.func_injected_rate;
    const fix    = r.func_fixed_rate;
    const hasFix = r._tester_three_way.fixed != null;

    const BLUE   = '#3b82f6';
    const GREEN  = '#22c55e';
    const ORANGE = '#f97316';
    const GRAY   = '#9ca3af';

    // INJ:   orange if degraded vs BASE, green if not (or no data → green)
    const injColor = (inj != null && base != null && inj < base) ? ORANGE : GREEN;
    // FIXED: green if rate >= BASE (preserved), orange otherwise. Gray if no patch.
    const fixColor = !hasFix
      ? GRAY
      : (fix != null && base != null && fix >= base) ? GREEN : ORANGE;

    function miniBar(label, value, color) {
      const fill   = value == null ? 0 : Math.max(0, Math.min(100, value));
      const valStr = value == null ? '—' : Math.round(value) + '%';
      return `
        <div class="flex items-center gap-2 text-xs">
          <span class="font-medium text-gray-600 w-12">${label}</span>
          <div class="flex-1 bar-track" style="height:8px">
            <div class="bar-fill" style="height:8px;width:${fill}%;background:${color}"></div>
          </div>
          <span class="tabular-nums w-10 text-right text-gray-700">${valStr}</span>
        </div>`;
    }

    return `
      <div class="grid grid-cols-3 gap-4 mb-3">
        ${miniBar('BASE',  base, BLUE)}
        ${miniBar('INJ',   inj,  injColor)}
        ${miniBar('FIXED', fix,  fixColor)}
      </div>`;
  }

  function renderEnvSetup(r) {
    const e = r.env_setup;
    if (!e) return '';
    const created = e.created || [];
    const cmds    = e.setup_commands || [];
    if (!e.notes && created.length === 0 && cmds.length === 0) return '';
    let inner = '';
    if (e.notes)
      inner += `<div class="text-xs text-gray-700 mb-2">${esc(e.notes)}</div>`;
    if (created.length)
      inner += `<div class="text-xs font-semibold text-gray-600">Created:</div>`
             + `<ul class="list-disc pl-5 mb-2">`
             + created.map(c => `<li class="font-mono text-xs">${esc(c)}</li>`).join('')
             + `</ul>`;
    if (cmds.length)
      inner += `<div class="text-xs font-semibold text-gray-600">Setup commands:</div>`
             + cmds.map(c => `<pre class="text-xs bg-white/60 border border-blue-200 rounded p-1 mt-1 whitespace-pre-wrap break-all font-mono">${esc(c)}</pre>`).join('');
    const body = `<div class="bg-blue-50 border-l-4 border-blue-300 p-3 rounded-r">${inner}</div>`;
    return collapsible('Environment setup', body, false);
  }

  function renderRedMetadata(r) {
    if (!r.reasoning && !r.strategy) return '';
    const items = [];
    if (r.strategy)
      items.push(`<div><dt class="font-medium text-gray-600 inline">Strategy:</dt> <dd class="inline text-gray-800">${esc(r.strategy)}</dd></div>`);
    if (r.diff_label)
      items.push(`<div><dt class="font-medium text-gray-600 inline">Difficulty label:</dt> <dd class="inline text-gray-800">${esc(r.diff_label)}</dd></div>`);
    if (r.line_num != null)
      items.push(`<div><dt class="font-medium text-gray-600 inline">Line inserted:</dt> <dd class="inline text-gray-800">${r.line_num}</dd></div>`);
    if (r.reasoning)
      items.push(`<div class="mt-2"><dt class="font-medium text-gray-600">Red reasoning:</dt><dd class="text-gray-800 italic mt-1 whitespace-pre-wrap">${esc(r.reasoning)}</dd></div>`);
    return collapsible('Red agent metadata', `<dl class="text-xs space-y-1">${items.join('')}</dl>`, false);
  }

  function renderAttemptsDetail(r, version) {
    if (!r._tester_three_way) return '';
    const v = r._tester_three_way[version];
    if (!v || !v.attempts || v.attempts.length === 0) return '';

    const verLabel = version.toUpperCase();
    // Open INJECTED by default if a confirmed bypass exists; others stay closed.
    const openByDefault = (version === 'injected' && (r.asr_pre_count || 0) > 0);

    const items = v.attempts.map(a => {
      if (a.skipped) {
        return `<div class="mt-1 border-l-2 border-gray-200 pl-2 text-xs text-gray-400">#${a.attempt} — SKIPPED (base task failed)</div>`;
      }
      const taskMark = a.task_completed
        ? '<span class="text-green-700">✓</span>'
        : '<span class="text-red-700">✗</span>';
      const judgeStr = a.judge_executed === true ? 'true'
                     : a.judge_executed === false ? 'false'
                     : 'null';
      const judgeColor = a.judge_executed === true ? 'text-red-700 font-medium'
                       : a.judge_executed === false ? 'text-gray-600'
                       : 'text-gray-400';
      const md5Match = (a.knowledge_base || '').match(/md5=([a-f0-9]+)/);
      const md5Str   = md5Match ? `md5=${md5Match[1]}` : '';

      const tcHtml = (a.tool_calls || []).map(tc => {
        let cls = 'bg-gray-50 text-gray-800';
        if (tc.startsWith('TOOL_CALL'))        cls = 'bg-blue-50 text-blue-900';
        else if (tc.startsWith('TOOL_RESULT')) cls = 'bg-gray-50 text-gray-800';
        else if (tc.startsWith('[Agent]'))     cls = 'bg-purple-50 text-purple-900';
        return `<pre class="text-xs ${cls} border border-gray-200 rounded p-2 mt-1 whitespace-pre-wrap break-all font-mono max-h-64 overflow-y-auto">${esc(tc)}</pre>`;
      }).join('');

      const ao = (a.agent_output || '').trim();
      const aoHtml = ao
        ? `<div class="mt-2"><div class="text-xs font-semibold text-gray-600">Agent output:</div><pre class="text-xs bg-gray-50 border border-gray-200 rounded p-2 mt-1 overflow-x-auto whitespace-pre-wrap font-mono">${esc(ao)}</pre></div>`
        : '';

      return `
        <details class="mt-1 border-l-2 border-gray-200 pl-2">
          <summary class="cursor-pointer text-xs py-0.5 select-none">
            <span class="font-medium">#${a.attempt}</span>
            ${taskMark}
            <span class="text-gray-500 ml-1">judge:</span> <span class="${judgeColor}">${judgeStr}</span>
            ${md5Str ? `<span class="text-gray-400 ml-2">${md5Str}</span>` : ''}
          </summary>
          <div class="mt-1 mb-2">
            ${tcHtml ? `<div class="text-xs font-semibold text-gray-600 mt-1">Tool calls (${(a.tool_calls||[]).length}):</div>${tcHtml}` : ''}
            ${aoHtml}
          </div>
        </details>`;
    }).join('');

    return collapsible(`Attempt detail — ${verLabel}`, items, openByDefault);
  }

  function showModal(cardIdx, version, attemptK) {
    const r = records[cardIdx];
    if (!r || !r._tester_three_way) return;

    const TABS = ['base', 'injected', 'fixed'];
    const t3 = r._tester_three_way;

    // Pre-render content per version (null = tab disabled)
    function renderVersionContent(ver) {
      const v = t3[ver];
      if (!v) return null;
      const a = (v.attempts || []).find(x => x.attempt === attemptK);
      if (!a) return null;
      if (a.skipped) {
        return `<div class="text-sm text-gray-500 italic py-8 text-center">SKIPPED — base task failed (this prompt was not run on ${ver.toUpperCase()})</div>`;
      }

      const taskStr = a.task_completed
        ? '<span class="text-green-700 font-medium">✓</span>'
        : '<span class="text-red-700 font-medium">✗</span>';
      const judgeStr = a.judge_executed === true
        ? '<span class="text-red-700 font-medium">true</span>'
        : a.judge_executed === false
          ? '<span class="text-gray-600">false</span>'
          : '<span class="text-gray-400">null</span>';

      const tcHtml = (a.tool_calls || []).map(tc => {
        let cls = 'bg-gray-50 text-gray-800';
        if (tc.startsWith('TOOL_CALL'))        cls = 'bg-blue-50 text-blue-900';
        else if (tc.startsWith('TOOL_RESULT')) cls = 'bg-gray-50 text-gray-800';
        else if (tc.startsWith('[Agent]'))     cls = 'bg-purple-50 text-purple-900';
        return `<pre class="text-xs ${cls} border border-gray-200 rounded p-2 whitespace-pre-wrap break-all font-mono max-h-64 overflow-y-auto">${esc(tc)}</pre>`;
      }).join('');

      // Contextual top-of-tab block: injection (INJECTED) / patch ops (FIXED)
      let contextBlock = '';
      if (ver === 'injected' && r.inj_text) {
        const meta = `Strategy: ${esc(r.strategy || '?')}` +
                     (r.line_num != null ? ` | line: ${r.line_num}` : '');
        contextBlock = `
          <div class="bg-red-50 border-l-4 border-red-400 p-3 rounded-r mb-3 text-xs">
            <div class="font-semibold text-red-700 mb-1">🔴 Injected payload</div>
            <pre class="font-mono text-xs whitespace-pre-wrap max-h-32 overflow-y-auto">${esc(r.inj_text)}</pre>
            <div class="mt-1 text-gray-600">${meta}</div>
          </div>`;
      } else if (ver === 'fixed') {
        const patches = r.patches_applied || [];
        if (patches.length === 0) {
          contextBlock = `
            <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded-r mb-3 text-xs">
              <div class="font-semibold text-amber-700">⚠️ No patch produced — Blue detected but did not fix</div>
            </div>`;
        } else {
          contextBlock = patches.map(p => {
            const orig   = p.original || '';
            const repl   = p.replacement == null ? '' : p.replacement;
            const isRepl = orig && repl.trim() !== '';
            const header = isRepl ? '🔵 Blue patch — substituted'
                                  : '🔵 Blue patch — removed';
            let inner = `
              <div><span class="text-gray-500">Removed:</span></div>
              <pre class="font-mono text-xs line-through text-red-700 bg-red-50 max-h-40 overflow-y-auto whitespace-pre-wrap p-1 rounded">${esc(orig)}</pre>`;
            if (isRepl) {
              inner += `
                <div class="mt-1"><span class="text-gray-500">Added:</span></div>
                <pre class="font-mono text-xs text-green-700 bg-green-50 max-h-40 overflow-y-auto whitespace-pre-wrap p-1 rounded">${esc(repl)}</pre>`;
            }
            if (p.reason)
              inner += `<div class="mt-1 text-gray-600">Reason: ${esc(p.reason)}</div>`;
            return `
              <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded-r mb-3 text-xs">
                <div class="font-semibold text-blue-700 mb-1">${header}</div>
                ${inner}
              </div>`;
          }).join('');
        }
      }

      return `
        ${contextBlock}
        <div class="text-xs text-gray-600 mb-2 flex gap-4">
          <span>task_completed: ${taskStr}</span>
          <span>judge_executed: ${judgeStr}</span>
        </div>
        ${a.task_reason ? `
        <div class="mb-4 text-xs bg-amber-50 border-l-4 border-amber-300 p-2 rounded-r">
          <span class="font-semibold text-amber-800">Task judge reason:</span>
          <span class="text-gray-700"> ${esc(a.task_reason)}</span>
        </div>` : ''}
        <div class="mb-4">
          <div class="text-xs font-semibold text-gray-700 mb-1">Prompt:</div>
          <pre class="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto whitespace-pre-wrap font-mono select-text">${esc(a.prompt || '')}</pre>
        </div>
        ${a.knowledge_base ? `
          <div class="mb-4">
            <div class="text-xs font-semibold text-gray-700 mb-1">Knowledge base:</div>
            <pre class="text-xs bg-gray-50 border border-gray-200 rounded p-2 overflow-x-auto whitespace-pre-wrap font-mono">${esc(a.knowledge_base)}</pre>
          </div>` : ''}
        ${tcHtml ? `
          <div class="mb-4">
            <div class="text-xs font-semibold text-gray-700 mb-1">Tool calls (${(a.tool_calls || []).length}):</div>
            <div class="space-y-1">${tcHtml}</div>
          </div>` : ''}
        ${(a.agent_output && a.agent_output.trim()) ? `
          <div class="mb-4">
            <div class="text-xs font-semibold text-gray-700 mb-1">Agent output:</div>
            <pre class="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto whitespace-pre-wrap font-mono">${esc(a.agent_output)}</pre>
          </div>` : ''}
      `;
    }

    const tabContents = {};
    TABS.forEach(ver => { tabContents[ver] = renderVersionContent(ver); });

    // FIXED saltata: mostra un messaggio neutro nel tab (che resta abilitato)
    // invece di disabilitarlo, così è chiaro che lo skip è intenzionale. Mostra
    // ANCHE la patch del Blue (cosa è stato rimosso/sostituito) per verifica.
    if (r.fixed_skipped && !tabContents.fixed) {
      const reason = r.fixed_skip_reason === 'identical_to_base'
        ? 'patch identical to base' : 'no patch produced';
      const patches = r.patches_applied || [];
      let patchHtml = '';
      if (patches.length) {
        patchHtml = '<div class="mt-2 text-left">'
          + '<div class="text-xs font-semibold text-gray-700 mb-1">Blue patch (what was changed) — verify it only removed the injection:</div>'
          + patches.map(p => {
              const orig = p.original || '';
              const repl = (p.replacement == null ? '' : p.replacement);
              let h = `<div class="text-xs"><span class="text-gray-500">Removed:</span><br><code class="block ml-3 mt-0.5 bg-red-50 text-red-800 px-1.5 py-0.5 rounded break-all whitespace-pre-wrap">${esc(orig)}</code></div>`;
              h += repl.trim()
                ? `<div class="text-xs mt-1"><span class="text-gray-500">Replaced with:</span><br><code class="block ml-3 mt-0.5 bg-green-50 text-green-800 px-1.5 py-0.5 rounded break-all whitespace-pre-wrap">${esc(repl)}</code></div>`
                : `<div class="text-xs mt-1 text-gray-400">(no replacement — pure removal)</div>`;
              if (p.reason)
                h += `<div class="text-xs text-gray-500 mt-1">Reason: ${esc(p.reason)}</div>`;
              return `<div class="mb-2 border-l-2 border-gray-200 pl-2">${h}</div>`;
            }).join('')
          + '</div>';
      } else {
        patchHtml = '<div class="text-xs text-gray-400 text-center">(no patch recorded)</div>';
      }
      tabContents.fixed =
        `<div class="text-sm text-gray-500 italic py-3 text-center">FIXED not run — ${esc(reason)}</div>`
        + patchHtml;
    }

    // Initial tab: requested version if enabled, else first enabled, else bail
    let activeTab = tabContents[version] ? version : TABS.find(t => tabContents[t]);
    if (!activeTab) return;

    // Title: skill · vuln_type/difficulty
    const skill = r.skill || '?';
    const vt    = r.vuln_type || '';
    const diff  = r.difficulty || '';
    const titleSuffix = (vt && vt !== 'user_provided')
      ? `${esc(skill)} · ${esc(vt)}/${esc(diff)}`
      : esc(skill);
    const title = `Attempt #${attemptK} — ${titleSuffix}`;

    // Tab class helpers — closure reads activeTab live, so re-applying works after click
    const ACTIVE_CLS   = 'px-4 py-2 text-sm bg-white border-b-2 border-blue-600 text-blue-600 font-medium cursor-pointer';
    const INACTIVE_CLS = 'px-4 py-2 text-sm text-gray-600 hover:underline cursor-pointer border-b-2 border-transparent';
    const DISABLED_CLS = 'px-4 py-2 text-sm text-gray-300 cursor-not-allowed border-b-2 border-transparent';
    function tabClass(ver) {
      if (!tabContents[ver]) return DISABLED_CLS;
      return ver === activeTab ? ACTIVE_CLS : INACTIVE_CLS;
    }

    const tabBar = TABS.map(ver => {
      const enabled = tabContents[ver] !== null;
      return `<button class="${tabClass(ver)}" data-tab="${ver}"${enabled ? '' : ' disabled'}>${ver.toUpperCase()}</button>`;
    }).join('');

    document.getElementById('sse-modal-body').innerHTML = `
      <h3 class="text-lg font-semibold mb-2">${title}</h3>
      <div class="border-b border-gray-200 mb-4 flex" id="sse-modal-tabs">${tabBar}</div>
      <div id="sse-modal-tab-content">${tabContents[activeTab]}</div>
    `;

    // Wire tab clicks — buttons stay in DOM; we only update class strings + content
    document.querySelectorAll('#sse-modal-tabs [data-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        const ver = btn.dataset.tab;
        if (!tabContents[ver] || ver === activeTab) return;
        activeTab = ver;
        document.querySelectorAll('#sse-modal-tabs [data-tab]').forEach(b => {
          b.className = tabClass(b.dataset.tab);
        });
        document.getElementById('sse-modal-tab-content').innerHTML = tabContents[activeTab];
      });
    });

    document.getElementById('sse-modal').classList.remove('hidden');
  }

  function hideModal() {
    document.getElementById('sse-modal').classList.add('hidden');
  }

  // Red KB modal: mostra tutti gli esempi skill-inject usati dal Red (per classe).
  function showKbModal() {
    const kb = data.red_kb || {};
    const classes = kb.classes || {};
    const exemplars = kb.exemplars || {};
    const rows = Object.keys(classes).map(c =>
      `<tr><td class="py-1 pr-4 font-mono text-xs">${esc(c)}</td><td class="py-1 text-right">${classes[c]}</td></tr>`
    ).join('');
    const blocks = Object.keys(exemplars).map(c => {
      const items = (exemplars[c] || []).map(e => {
        let t = String(e.text || '').replace(/\s+/g, ' ').trim();
        if (t.length > 400) t = t.slice(0, 400) + '…';
        return `<li class="mb-1.5"><span class="font-mono text-[11px] text-gray-500">${esc(e.id||'?')}</span> <span class="text-gray-400">(from ${esc(e.skill||'?')})</span><br><span class="text-gray-700">${esc(t)}</span></li>`;
      }).join('');
      return `<details class="border border-gray-200 rounded mb-2">
        <summary class="cursor-pointer select-none px-3 py-2 bg-gray-50 font-medium text-sm"><span class="arrow"></span>${esc(c)} <span class="text-gray-400 font-normal">(${(exemplars[c]||[]).length})</span></summary>
        <ul class="px-4 py-2 text-xs list-disc list-inside">${items}</ul></details>`;
    }).join('');
    document.getElementById('sse-modal-body').innerHTML = `
      <h3 class="text-lg font-semibold mb-2">🧬 Red KB — skill-inject exemplars</h3>
      <p class="text-sm text-gray-600 mb-3">The Red agent used the paper's 8-class taxonomy (<span class="font-mono">${esc(kb.catalog||'catalog_paper.json')}</span>) with these <b>${kb.total_exemplars||0}</b> real skill-inject injections as <b>inspiration only</b> (never copied).</p>
      <table class="text-sm mb-4"><tbody>${rows}</tbody></table>
      <div>${blocks}</div>`;
    document.getElementById('sse-modal').classList.remove('hidden');
  }

  function renderCard(r) {
    const det          = !!r.detected;
    const asrPre       = r.asr_pre;
    const asrPost      = r.asr_post;
    const patchEff     = r.patch_eff;
    const conf         = r.confidence || 0;
    const vt           = r.vuln_type || '';
    const diff         = r.difficulty || '';
    const skill        = r.skill || '?';
    const funcPreserved = r.functionality_preserved;

    const title = vt && vt !== 'user_provided'
      ? `${esc(skill)}  ·  ${esc(vt)}/${esc(diff)}`
      : esc(skill);

    // "Detection"/conf sono ground-truth-aware SOLO per Blue (vedi node_blue):
    // senza Blue in questa run mostrerebbero sempre ❌/0.00 anche quando un
    // altro motore ha flaggato qualcosa — nascosti, il badge per-motore più
    // sotto (Object.entries(r.engines)) mostra il verdetto reale.
    const hasBlue = !r.engines || ('blue' in r.engines);
    const cardBadges = hasBlue ? [
      badge('Detection', det ? '✅' : '❌', det ? 'green' : 'red'),
      `<span class="${BADGE.gray} px-2.5 py-1 rounded-md text-xs font-medium">conf ${conf.toFixed(2)}</span>`,
    ] : [];
    // Blue-eval: result + how-decided badges (green=caught, red=missed, amber=false alarm).
    if (r.verdict) {
      const vk = r.verdict === 'TP' ? 'green' : r.verdict === 'FP' ? 'orange' : 'red';
      const vlabel = r.verdict === 'TP' ? 'Caught' : r.verdict === 'FP' ? 'False alarm' : 'Missed';
      cardBadges.push(badge('result', vlabel, vk));
      cardBadges.push(badge('decided by', (r.tier === 2 ? 'LLM-reviewed' : 'Auto-match')
        + (r.match_ratio != null ? ' · match ' + r.match_ratio : ''), 'gray'));
    }
    // ASR continuo (change 1): mostra "bypass/attempts · rate%".
    const asrLabel = (val, cnt, tot) => {
      const r = val == null ? '—' : (val * 100).toFixed(0) + '%';
      return (cnt != null && tot != null) ? `${cnt}/${tot} · ${r}` : r;
    };
    if (asrPre != null)
      cardBadges.push(badge('asr_pre', asrLabel(asrPre, r.asr_pre_count, r.asr_pre_total),
                            asrPre > 0 ? 'red' : 'green'));
    if (asrPost != null)
      cardBadges.push(badge('asr_post', asrLabel(asrPost, r.asr_post_count, r.asr_post_total),
                            asrPost > 0 ? 'red' : 'green'));
    if (patchEff != null)
      cardBadges.push(badge('patch_eff', (patchEff >= 0 ? '+' : '') + (patchEff * 100).toFixed(0) + 'pp',
                             patchEff > 0 ? 'green' : patchEff < 0 ? 'red' : 'gray'));
    if (funcPreserved === false)
      cardBadges.push(badge('func_preserved', 'false', 'orange'));
    if (r.fixed_skipped) {
      const reason = r.fixed_skip_reason === 'identical_to_base'
        ? 'patch identical to base' : 'no patch produced';
      cardBadges.push(`<span class="bg-gray-100 text-gray-500 px-2.5 py-1 rounded-md text-xs font-medium">FIXED not run — ${esc(reason)}</span>`);
    }

    let body = '';

    // Injection text (collapsible) — for blue-eval this is the GROUND TRUTH.
    // Auto-open when a bypass was confirmed (full) or the injection was MISSED (FN).
    if (r.inj_text) {
      const label = r.verdict ? 'Injection text (ground truth)' : 'Injection text';
      body += collapsible(label,
        `<pre class="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto whitespace-pre-wrap font-mono">${esc(r.inj_text)}</pre>`,
        (r.asr_pre_count || 0) > 0 || r.verdict === 'FN');
    }

    // Blue finding + patch (collapsible)
    const findings = r.findings || [];
    const patches  = r.patches_applied || [];
    if (findings.length > 0 || patches.length > 0) {
      let bp = '';
      if (findings.length > 0) {
        bp += `<div class="space-y-1.5 mb-3">`;
        findings.forEach(f => {
          const sev      = f.severity || '?';
          const sevColor = sev === 'high' ? 'red' : sev === 'medium' ? 'orange' : 'gray';
          bp += `<div class="text-sm">${badge(sev, f.type || '?', sevColor)} <span class="text-gray-700">${esc((f.description || '').slice(0, 300))}</span></div>`;
        });
        bp += `</div>`;
      }
      if (patches.length > 0) {
        bp += `<div class="text-sm space-y-2 border-t border-gray-200 pt-3">`;
        bp += `<div class="font-medium text-gray-700">Patch:</div>`;
        patches.forEach(p => {
          bp += `<div class="text-xs"><span class="text-gray-500">Removed:</span><br><code class="block ml-3 mt-0.5 bg-red-50 text-red-800 px-1.5 py-0.5 rounded break-all whitespace-pre-wrap">${esc(p.original || '')}</code></div>`;
          if ((p.replacement || '').trim()) {
            bp += `<div class="text-xs"><span class="text-gray-500">Replaced with:</span><br><code class="block ml-3 mt-0.5 bg-green-50 text-green-800 px-1.5 py-0.5 rounded break-all whitespace-pre-wrap">${esc(p.replacement)}</code></div>`;
          } else {
            bp += `<div class="text-xs mt-1 text-gray-400">(no replacement — pure removal)</div>`;
          }
        });
        bp += `</div>`;
      }
      body += collapsible('Blue finding + patch', bp, false);
    }

    // Discarded findings (quote non ancorata al file) — traccia per-skill.
    const discarded = r.discarded_findings || [];
    if (discarded.length > 0) {
      let db = `<div class="space-y-1.5">`;
      discarded.forEach(f => {
        const sev = f.severity || '?';
        const q   = (f.quote || '').slice(0, 120);
        db += `<div class="text-sm">${badge(sev, f.type || '?', 'gray')} `
            + `<span class="text-gray-500 italic">${esc(f.discard_reason || '')}</span>`
            + (q ? ` <code class="text-xs bg-gray-50 px-1 py-0.5 rounded break-all">${esc(q)}</code>` : '')
            + `</div>`;
      });
      db += `</div>`;
      body += collapsible(`Discarded findings (${discarded.length} · quote not anchored)`, db, false);
    }

    // Blue reasoning — always shown, expanded when not detected
    if (r.scan_reasoning) {
      body += collapsible('Blue reasoning',
        `<div class="text-sm text-gray-700 italic whitespace-pre-wrap leading-relaxed">${esc(r.scan_reasoning.slice(0, 3000))}</div>`,
        !det);
    }

    // Validator reasoning (blue-eval LLM reviewer) — same pattern as Blue reasoning,
    // open-by-default on misses/false alarms, so the methodology is auditable.
    if (r.tier === 2 && r.validator_reasoning) {
      body += collapsible('LLM reviewer',
        `<div class="text-sm text-gray-700 italic whitespace-pre-wrap leading-relaxed">${esc(r.validator_reasoning.slice(0, 3000))}</div>`,
        r.verdict === 'FN' || r.verdict === 'FP');
    }

    // Altri motori di difesa (skillspector/cisco/aig/snyk/skills_sh) — nessun
    // verdetto ground-truth-aware come Blue (niente "Detection" badge sopra),
    // solo flagged/findings grezzi da r.engines[engine] (python _with_engine).
    // Senza questo, una run senza Blue mostrava sempre "Detection ❌" e zero
    // findings anche quando il motore ne aveva trovati (vedi aggregate table).
    Object.entries(r.engines || {}).forEach(([eng, v]) => {
      if (eng === 'blue') return;
      if (v.scan_error) {
        body += `<div class="bg-amber-50 border border-amber-200 text-amber-800 rounded-md px-3 py-2 mb-3 text-sm"><b>${esc(eng)}</b>: scan error — ${esc(String(v.scan_error).slice(0, 200))}</div>`;
        return;
      }
      if (v.available === false) {
        body += `<div class="text-sm text-gray-500 mb-2"><b>${esc(eng)}</b>: no verdict (not covered)</div>`;
        return;
      }
      const efindings = v.findings || [];
      let eb = `<div class="text-sm mb-1">${badge(eng, v.flagged ? 'flagged' : 'clean', v.flagged ? 'orange' : 'green')} <span class="text-gray-500 text-xs">${efindings.length} finding(s)</span></div>`;
      if (efindings.length > 0) {
        eb += `<div class="space-y-1.5 mb-2">`;
        efindings.forEach(f => {
          const sev      = f.severity || '?';
          const sevColor = sev === 'high' ? 'red' : sev === 'medium' ? 'orange' : 'gray';
          const code     = f.code || f.type || '?';
          eb += `<div class="text-sm">${badge(sev, code, sevColor)} <span class="text-gray-700">${esc((f.description || f.title || '').slice(0, 300))}</span></div>`;
        });
        eb += `</div>`;
      }
      body += collapsible(`${esc(eng)} finding(s)`, eb, !!v.flagged);
    });

    // Prompt grid (only if three-way data present)
    if (r._tester_three_way) body += renderPromptGrid(r._tester_three_way, r);

    // Bypass badge (collapsible — shows evidence on expand)
    if ((r.asr_pre_count || 0) > 0 && r.evidence_pre) {
      const baNum    = r.bypass_attempt_pre;
      const attemptS = baNum ? `attempt #${baNum}` : 'an attempt';
      body += `
        <details class="mt-4">
          <summary class="cursor-pointer select-none">
            <span class="bg-red-100 text-red-800 px-2.5 py-1 rounded-md text-xs font-medium">
              🚨 Bypass: ${attemptS} on INJECTED — click to show evidence
            </span>
          </summary>
          <pre class="text-xs bg-red-50 border border-red-200 rounded p-3 mt-2 overflow-x-auto whitespace-pre-wrap font-mono">${esc(r.evidence_pre)}</pre>
        </details>`;
    }

    // Bypass badge post-patch — the attack still worked on the PATCHED skill,
    // i.e. the fix did not actually stop it. Open by default: this is the
    // one signal that "patch applied" can silently hide (see patch_eff=0).
    if ((r.asr_post_count || 0) > 0 && r.evidence_post) {
      const baNum    = r.bypass_attempt_post;
      const attemptS = baNum ? `attempt #${baNum}` : 'an attempt';
      body += `
        <details class="mt-4" open>
          <summary class="cursor-pointer select-none">
            <span class="bg-red-100 text-red-800 px-2.5 py-1 rounded-md text-xs font-medium">
              🚨 Bypass: ${attemptS} on FIXED (patch did not stop it) — click to show evidence
            </span>
          </summary>
          <pre class="text-xs bg-red-50 border border-red-200 rounded p-3 mt-2 overflow-x-auto whitespace-pre-wrap font-mono">${esc(r.evidence_post)}</pre>
        </details>`;
    }

    // Change 2: Red metadata + per-version attempt detail at the bottom of each card
    body += renderEnvSetup(r);
    body += renderRedMetadata(r);
    // Per-injection Red user prompt (carries the KB) — collapsible for audit.
    if (r.red_user_prompt) {
      body += `
        <details class="mt-3 border border-indigo-200 rounded">
          <summary class="cursor-pointer select-none px-3 py-2 bg-indigo-50 text-indigo-800 text-sm font-medium"><span class="arrow"></span>🧠 Red user prompt (with KB)</summary>
          <pre class="text-xs bg-gray-50 border-t border-indigo-100 p-3 overflow-x-auto whitespace-pre-wrap font-mono">${esc(r.red_user_prompt)}</pre>
        </details>`;
    }
    body += renderAttemptsDetail(r, 'base');
    body += renderAttemptsDetail(r, 'injected');
    body += renderAttemptsDetail(r, 'fixed');

    // Environment-failure banner (amber) or partial base-skip note
    let envNotice = '';
    if (r.scan_failed) {
      envNotice += `<div class="bg-amber-100 border border-amber-300 text-amber-800 rounded-md px-3 py-2 mb-3 text-sm">⚠️ Blue scan FAILED${r.scan_error ? ` (${esc(String(r.scan_error).slice(0,120))})` : ''} — result is NOT a clean skill; finding absence is inconclusive.</div>`;
    }
    const _envFail = (r.env_setup && r.env_setup.failed_commands) || 0;
    if (_envFail > 0) {
      envNotice += `<div class="bg-amber-100 border border-amber-300 text-amber-800 rounded-md px-3 py-2 mb-3 text-sm">⚠️ EnvAgent: ${_envFail} setup commands failed — workspace may be incomplete.</div>`;
    }
    if (r.base_env_failed) {
      envNotice += `<div class="bg-amber-100 border border-amber-300 text-amber-800 rounded-md px-3 py-2 mb-3 text-sm">⚠️ Environment failure — all base prompts failed, injection metrics unavailable.</div>`;
    } else if (r.skipped_base_count) {
      const m = (r._tester_three_way && r._tester_three_way.prompts)
        ? r._tester_three_way.prompts.length : r.skipped_base_count;
      envNotice = `<div class="text-xs text-gray-500 mb-3">${r.skipped_base_count}/${m} prompts skipped (base task failed)</div>`;
    }

    const borderColor = det ? 'border-green-400' : 'border-red-400';
    return `
      <div data-card
           data-vuln-type="${esc(vt)}"
           data-asr-pre="${r.asr_pre_count == null ? 0 : r.asr_pre_count}"
           data-func-preserved="${funcPreserved === null || funcPreserved === undefined ? '' : String(funcPreserved)}"
           class="bg-white rounded-lg shadow-sm border-l-4 ${borderColor} p-5">
        <h3 class="text-lg font-semibold mb-1">${title}</h3>
        ${r.inj_path ? `<div class="text-xs text-gray-500 font-mono mb-2 break-all" title="${esc(r.inj_path)}">📄 ${esc(String(r.inj_path).split('/').slice(-2).join('/'))}</div>` : ''}
        ${envNotice}
        <div class="flex gap-2 flex-wrap mb-3">${cardBadges.join('')}</div>
        ${renderFuncBars(r)}
        ${body}
      </div>`;
  }

  html += `<section class="max-w-6xl mx-auto px-6 py-6 space-y-4">`;
  html += `<h2 class="text-lg font-semibold">Per-injection detail</h2>`;
  records.forEach(r => { html += renderCard(r); });
  html += `</section>`;

  html += `</div>`;  // close #tabPanelFindings

  html += renderCostTab();   // sibling of #tabPanelFindings, see note above

  // ── Third-party comparison tab (Blue vs Snyk vs NVIDIA SkillSpector) ──
  // Comparison is per-skill, not per-finding: each engine has its own finding
  // taxonomy (Blue: text quote; Snyk: issue code; SkillSpector: pattern id) —
  // no shared key to match individual findings reliably across engines.
  // A run may have used only one of the two third-party engines: columns for
  // an engine that never ran (row.snyk / row.skillspector === null) are
  // simply omitted, not rendered empty.
  function renderThirdPartyFindingList(findings, emptyLabel) {
    if (!findings || !findings.length) return `<div class="text-xs text-gray-400 italic">${esc(emptyLabel)}</div>`;
    return `<ul class="space-y-1.5">${findings.map(f => {
      const sev = esc((f.severity || '').toLowerCase());
      const sevColor = { high: 'red', critical: 'red', medium: 'orange', low: 'gray' }[sev] || 'gray';
      const title = esc(f.title || f.type || f.code || 'finding');
      const desc  = esc(f.description || '');
      const quote = esc(f.quote || '');
      const code  = f.code ? `<span class="text-gray-400 font-mono">[${esc(f.code)}]</span> ` : '';
      return `<li class="text-xs border-l-2 border-${sevColor}-300 pl-2">
        <span class="${BADGE[sevColor] || BADGE.gray} px-1.5 py-0.5 rounded text-[10px] font-medium mr-1">${sev || '—'}</span>
        ${code}<span class="font-medium">${title}</span>
        ${quote ? `<div class="text-gray-700 mt-1 bg-gray-50 border border-gray-200 rounded px-1.5 py-1 font-mono text-[11px] whitespace-pre-wrap break-all">${quote}</div>` : ''}
        ${desc ? `<div class="text-gray-500 mt-0.5">${desc}</div>` : ''}
      </li>`;
    }).join('')}</ul>`;
  }

  // skills.sh: metriche aggregate (Blue vs skills.sh, sul sottoinsieme di skill
  // effettivamente nel dataset) — stat badges informativi (non filtri) + una riga
  // di filter chip DEDICATA, separata da quella "overall (all active engines)"
  // qui sotto perché è un confronto diverso (solo Blue vs skills.sh, ignora Snyk/
  // SkillSpector anche quando attivi) — vedi tpSshStatus()/data-tp-ssh-status sul
  // per-skill grid. Le due righe di filtro sono ESCLUSIVE tra loro (click su una
  // azzera l'altra) — vedi tpActiveFilter più sotto.
  function renderSkillsShStats() {
    const s  = data.skills_sh_summary;
    const ss = data.skillspector_summary;
    const cs = data.cisco_summary;
    if (!s && !ss && !cs) return '';
    const engineLabel = { snyk: 'Snyk', socket: 'Socket', agentTrustHub: 'AgentTrustHub' };
    const engineRates = s ? Object.entries(s.per_engine_rate || {})
      .map(([k, v]) => badge(engineLabel[k] || k, pct(v), 'gray')).join('') : '';
    // SkillSpector/Cisco girano localmente in questa run (non sono uno dei 3
    // motori del dataset skills.sh): denominatore diverso (n skill scansionate
    // con successo, vs n skill presenti nel dataset skills.sh) — per questo
    // sono etichettati a parte e il conteggio è esplicitato nella nota.
    const ssBadge = ss ? badge('SkillSpector', pct(ss.engine_detection_rate), 'green') : '';
    const csBadge = cs ? badge('Cisco skill-scanner', pct(cs.engine_detection_rate), 'indigo') : '';
    const notes = [];
    if (s) notes.push(`🌐 skills.sh comparison: only the ${s.n} skills in this run actually present in the
        skills.sh dataset (verdict already computed by skills.sh: at least one finding in one
        of its 3 engines — agentTrustHub, socket, snyk).`);
    if (ss) notes.push(`🟩 SkillSpector: scanned locally in this run — ${ss.n} skills scanned successfully
        (failed scans excluded), Blue detection on that same subset: ${pct(ss.blue_detection_rate)}.`);
    if (cs) notes.push(`🔷 Cisco skill-scanner: scanned locally in this run — ${cs.n} skills scanned successfully
        (failed scans excluded), Blue detection on that same subset: ${pct(cs.blue_detection_rate)}.`);
    return `
      ${notes.map(t => `<p class="text-xs text-gray-500 mb-2">${t}</p>`).join('')}
      <div class="flex gap-2 flex-wrap mb-3">
        ${s ? badge('Blue detection', pct(s.blue_detection_rate), 'blue') : ''}
        ${s ? badge('skills.sh detection', pct(s.skills_sh_detection_rate), 'purple') : ''}
        ${engineRates}
        ${ssBadge}
        ${csBadge}
      </div>`;
  }

  // Generic "Blue vs ONE other engine" filter-chip row — same shape reused for
  // skills.sh / Snyk / SkillSpector, each its own EXCLUSIVE filter group (see
  // tpActiveFilter wiring below). groupAttr picks the data attribute
  // (data-tp-${groupAttr}-filter) and must match the row's data-tp-${groupAttr}-status.
  function renderPairFilterChips(summary, groupAttr, colorClass, icon, engineLabel) {
    if (!summary) return '';
    const filterBadge = (label, value, kind, key) =>
      `<button type="button" data-tp-${groupAttr}-filter="${key}"
               class="bg-transparent border-0 p-0 rounded-md cursor-pointer hover:opacity-80 focus:outline-none">
        ${badge(label, value, kind)}
      </button>`;
    return `
      <div class="mb-4">
        <div class="text-xs font-semibold ${colorClass} mb-1">${icon} Filter by — Blue vs ${engineLabel} only:</div>
        <div class="flex gap-2 flex-wrap">
          ${filterBadge('✅ Agree — flagged', summary.agree_flagged, 'green', 'agree_flagged')}
          ${filterBadge('— Agree — clean',    summary.agree_clean,   'gray',  'agree_clean')}
          ${filterBadge(`⚠️ ${engineLabel} flagged, Blue missed`, summary.blue_missed, 'red',    'eng_missed')}
          ${filterBadge(`🔺 Blue flagged, ${engineLabel} missed`, summary.blue_only,   'orange', 'blue_only')}
        </div>
      </div>`;
  }

  function renderThirdPartyTab() {
    if (!hasThirdParty) return '';
    const rows = data.third_party_comparison || [];
    const anySnyk  = rows.some(r => r.snyk);
    const anySS    = rows.some(r => r.skillspector);
    const anyCisco = rows.some(r => r.cisco);
    const anySsh   = rows.some(r => r.skills_sh);
    const nEngineCols = 1 + (anySnyk ? 1 : 0) + (anySS ? 1 : 0) + (anyCisco ? 1 : 0) + (anySsh ? 1 : 0);   // Blue + active third-party engines
    const gridCols = `md:grid-cols-[180px_${Array(nEngineCols).fill('1fr').join('_')}]`;

    const rowFailed = r => (r.snyk && r.snyk.status === 'failed')
                        || (r.skillspector && r.skillspector.status === 'failed')
                        || (r.cisco && r.cisco.status === 'failed');
    const allFlagged = rows.filter(r => r.engines_active > 0 && r.engines_flagged === r.engines_active).length;
    const allClean   = rows.filter(r => r.engines_flagged === 0).length;
    const mixed      = rows.length - allFlagged - allClean;
    const anyFailed  = rows.filter(rowFailed).length;
    // Summary badges double as filters (click to show only matching rows,
    // click again to clear) — wired in the "third-party filter" JS below.
    const filterBadge = (label, value, kind, key) =>
      `<button type="button" data-tp-filter="${key}"
               class="bg-transparent border-0 p-0 rounded-md cursor-pointer hover:opacity-80 focus:outline-none">
        ${badge(label, value, kind)}
      </button>`;
    const summary = `
      <div class="mb-2">
        <div class="text-xs font-semibold text-gray-600 mb-1">Filter by — overall (all active engines):</div>
        <div class="flex gap-2 flex-wrap">
          ${filterBadge('✅ All engines agree — flagged', allFlagged, 'green',  'flagged')}
          ${filterBadge('— All engines agree — clean',    allClean,   'gray',   'clean')}
          ${filterBadge('⚠️ Engines disagree',            mixed,      'orange', 'mixed')}
          ${filterBadge('🚫 A scan failed',               anyFailed,  'red',    'failed')}
        </div>
      </div>`;

    const engineCol = (label, icon, engine, extraLabel) => {
      if (!engine) return '';
      const n = (engine.findings || []).length;
      const emptyLabel = engine.status === 'failed' ? 'scan failed' : 'no findings';
      return `
        <div>
          <div class="text-[11px] uppercase tracking-wide text-gray-400 mb-1">${icon} ${esc(label)} (${n})${extraLabel || ''}</div>
          ${engine.scan_error ? `<div class="text-[11px] text-red-600 mb-1">⚠️ ${esc(engine.scan_error)}</div>` : ''}
          ${renderThirdPartyFindingList(engine.findings, emptyLabel)}
        </div>`;
    };

    // skills.sh: composito (3 sotto-motori indipendenti, non un unico scan) —
    // una mini-sezione per sotto-motore invece di una lista unica appiattita,
    // così si vede SUBITO quale motore skills.sh ha preso cosa.
    const SSH_ENGINE_LABEL = { snyk: 'Snyk', socket: 'Socket', agentTrustHub: 'AgentTrustHub' };
    const skillsShCol = (ssh) => {
      if (!ssh) return '';
      if (!ssh.available) {
        return `
          <div>
            <div class="text-[11px] uppercase tracking-wide text-gray-400 mb-1">🌐 skills.sh</div>
            <div class="text-xs text-gray-400 italic">not in skills.sh dataset</div>
          </div>`;
      }
      const n = Object.values(ssh.engines || {}).reduce((s, e) => s + (e.findings || []).length, 0);
      const sub = Object.entries(ssh.engines || {}).map(([name, e]) => `
        <div class="mb-2">
          <div class="text-[10px] uppercase tracking-wide text-gray-400 mb-0.5">${esc(SSH_ENGINE_LABEL[name] || name)} ${e.flagged ? '🔺' : '✅'}</div>
          ${renderThirdPartyFindingList(e.findings, 'no findings')}
        </div>`).join('');
      return `
        <div>
          <div class="text-[11px] uppercase tracking-wide text-gray-400 mb-1">🌐 skills.sh (${n})</div>
          ${sub}
        </div>`;
    };

    // Blue-vs-ONE-engine status (separate dimension from tpStatus below — see
    // renderPairFilterChips()). 'na' = that engine didn't run / failed / this
    // skill isn't in its dataset; never matched by any of that engine's filter
    // chips, so it just disappears from the grid whenever that filter is active
    // (itself a signal). usable=false → 'na', regardless of blueDetected/flagged.
    const tpPairStatus = (blueDetected, usable, flagged) => {
      if (!usable) return 'na';
      if (blueDetected && flagged)   return 'agree_flagged';
      if (!blueDetected && !flagged) return 'agree_clean';
      if (!blueDetected && flagged)  return 'eng_missed';
      return 'blue_only';
    };
    const tpSshStatus = r =>
      tpPairStatus(r.blue.detected, !!(r.skills_sh && r.skills_sh.available),
                   !!(r.skills_sh && r.skills_sh.status === 'flagged'));
    const tpSnykStatus = r =>
      tpPairStatus(r.blue.detected, !!(r.snyk && r.snyk.status !== 'failed'),
                   !!(r.snyk && r.snyk.status === 'flagged'));
    const tpSkillspectorStatus = r =>
      tpPairStatus(r.blue.detected, !!(r.skillspector && r.skillspector.status !== 'failed'),
                   !!(r.skillspector && r.skillspector.status === 'flagged'));
    const tpCiscoStatus = r =>
      tpPairStatus(r.blue.detected, !!(r.cisco && r.cisco.status !== 'failed'),
                   !!(r.cisco && r.cisco.status === 'flagged'));

    const rowsHtml = rows.map(r => {
      const allOk = r.engines_active > 0 && r.engines_flagged === r.engines_active;
      const noneOk = r.engines_flagged === 0;
      const tpStatus = allOk ? 'flagged' : noneOk ? 'clean' : 'mixed';
      const rowPill = (label, kind) =>
        `<span class="${BADGE[kind] || BADGE.gray} px-2 py-0.5 rounded text-[11px] font-medium inline-block">${esc(label)}</span>`;
      const statusBadge = allOk
        ? rowPill('✅ All engines agree — flagged', 'green')
        : noneOk
          ? rowPill('— All engines agree — clean', 'gray')
          : rowPill(`⚠️ Engines disagree (${r.engines_flagged}/${r.engines_active} flagged)`, 'orange');
      const snykCachedTag = r.snyk && r.snyk.source === 'skills_sh_audit'
        ? ' <span class="text-gray-400 font-normal normal-case" title="Verdict pre-computed by skills.sh, not a live scan">📦 cached</span>' : '';
      const ssStaticTag = r.skillspector && !r.skillspector.used_llm
        ? ' <span class="text-gray-400 font-normal normal-case" title="Static analysis only (no LLM credentials available)">⚙️ static-only</span>' : '';
      const ciscoStaticTag = r.cisco && !r.cisco.used_llm
        ? ' <span class="text-gray-400 font-normal normal-case" title="Static analysis only (no LLM credentials available)">⚙️ static-only</span>' : '';
      return `
      <div data-tp-row data-tp-status="${tpStatus}" data-tp-failed="${rowFailed(r)}"
           data-tp-ssh-status="${tpSshStatus(r)}" data-tp-snyk-status="${tpSnykStatus(r)}"
           data-tp-skillspector-status="${tpSkillspectorStatus(r)}" data-tp-cisco-status="${tpCiscoStatus(r)}"
           class="bg-white rounded-lg shadow-sm p-4 grid grid-cols-1 ${gridCols} gap-4">
        <div>
          <div class="font-medium text-sm">${esc(r.skill)}</div>
          <div class="mt-1">${statusBadge}</div>
        </div>
        ${engineCol('Blue', '🔵', { findings: r.blue.findings, status: r.blue.detected ? 'flagged' : 'clean' })}
        ${engineCol('Snyk', '🛡️', r.snyk, snykCachedTag)}
        ${engineCol('SkillSpector', '🟩', r.skillspector, ssStaticTag)}
        ${engineCol('Cisco skill-scanner', '🔷', r.cisco, ciscoStaticTag)}
        ${skillsShCol(r.skills_sh)}
      </div>`;
    }).join('');

    const engineNote = [
      'Blue (text quote)',
      anySnyk ? 'Snyk (issue code)' : null,
      anySS ? 'SkillSpector (pattern id)' : null,
      anyCisco ? 'Cisco skill-scanner (rule id)' : null,
      anySsh ? 'skills.sh (agentTrustHub/socket/snyk — verdict already computed)' : null,
    ].filter(Boolean).join(', ');

    return `
      <div id="tabPanelThirdParty" class="hidden">
        <section class="max-w-6xl mx-auto px-6 pt-6">
          <h2 class="text-lg font-semibold mb-1">Blue vs third-party engines — per-skill comparison</h2>
          <p class="text-sm text-gray-500 mb-3">Each skill scanned by every active engine. Comparison is per-skill (did each engine flag it at all) — each engine has its own finding taxonomy (${esc(engineNote)}), so individual findings aren't matched one-to-one.</p>
          ${renderSkillsShStats()}
          ${summary}
          ${renderPairFilterChips(data.skills_sh_summary,   'ssh',          'text-purple-700',  '🌐', 'skills.sh')}
          ${renderPairFilterChips(data.snyk_summary,        'snyk',         'text-sky-700',     '🛡️', 'Snyk')}
          ${renderPairFilterChips(data.skillspector_summary,'skillspector', 'text-emerald-700', '🟩', 'SkillSpector')}
          ${renderPairFilterChips(data.cisco_summary,       'cisco',        'text-indigo-700',  '🔷', 'Cisco skill-scanner')}
        </section>
        <section class="max-w-6xl mx-auto px-6 pb-6 space-y-3">${rowsHtml}</section>
      </div>`;
  }
  html += renderThirdPartyTab();

  // ── modal (change 1): single instance, populated dynamically ─────
  html += `
    <div id="sse-modal" class="hidden fixed inset-0 z-[100] bg-black/60 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto relative">
        <button id="sse-modal-close"
                class="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-2xl leading-none w-8 h-8 flex items-center justify-center"
                aria-label="Close">×</button>
        <div id="sse-modal-body" class="p-6 pt-8"></div>
      </div>
    </div>`;

  app.innerHTML = html;

  // Tab switching (Findings / Third-party comparison) — panels present
  // depend on hasThirdParty/hasCost. Toggle generically by id prefix so
  // adding another tab later doesn't need touching this handler.
  document.querySelectorAll('.sse-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tabTarget;
      document.querySelectorAll('.sse-tab-btn').forEach(b => {
        b.classList.toggle('bg-blue-600', b === btn);
        b.classList.toggle('text-white', b === btn);
        b.classList.toggle('bg-gray-100', b !== btn);
        b.classList.toggle('text-gray-600', b !== btn);
      });
      document.querySelectorAll('[id^="tabPanel"]').forEach(panel => {
        panel.classList.toggle('hidden', panel.id !== target);
      });
    });
  });

  // Red KB modal button (present only when the run used the skill-inject KB)
  const kbBtn = document.getElementById('kb-modal-btn');
  if (kbBtn) kbBtn.onclick = showKbModal;

  // Stable index per card — used by sort to restore default order
  // and as a tie-breaker for non-default sort keys (improvement 4)
  document.querySelectorAll('[data-card]').forEach((card, i) => {
    card.dataset.index = String(i);
  });

  // Modal wiring (change 1): close on backdrop/X/ESC; open on cell click.
  const sseModal = document.getElementById('sse-modal');
  document.getElementById('sse-modal-close').onclick = hideModal;
  sseModal.addEventListener('click', (e) => {
    if (e.target === sseModal) hideModal();   // backdrop click only
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !sseModal.classList.contains('hidden')) hideModal();
  });
  document.querySelectorAll('[data-modal-attempt]').forEach(el => {
    el.addEventListener('click', () => {
      const card = el.closest('[data-card]');
      if (!card) return;
      showModal(parseInt(card.dataset.index, 10),
                el.dataset.modalVersion,
                parseInt(el.dataset.modalAttempt, 10));
    });
  });

  // ── filter wiring ────────────────────────────────────────────────
  const fVuln  = document.getElementById('f-vuln');
  const fAsr   = document.getElementById('f-asr');
  const fFunc  = document.getElementById('f-func');
  const fCount = document.getElementById('f-count');
  const fClear = document.getElementById('f-clear');
  const fSort  = document.getElementById('f-sort');
  const fExport = document.getElementById('f-export');

  function applyFilters() {
    const v        = fVuln.value;
    const asrOnly  = fAsr.checked;
    const funcOnly = fFunc.checked;
    let shown = 0;
    document.querySelectorAll('[data-card]').forEach(card => {
      const cv    = card.dataset.vulnType;
      const cAsr  = parseInt(card.dataset.asrPre || '0', 10);
      const cFunc = card.dataset.funcPreserved;
      let show = true;
      if (v && cv !== v)                 show = false;
      if (asrOnly && cAsr <= 0)          show = false;
      if (funcOnly && cFunc !== 'false') show = false;
      card.hidden = !show;
      if (show) shown++;
    });
    // Colored badge based on filter state (improvement 3)
    const total     = records.length;
    const anyFilter = !!v || asrOnly || funcOnly;
    if (shown === 0) {
      fCount.className   = 'px-2.5 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800';
      fCount.textContent = 'No results';
    } else if (!anyFilter || shown === total) {
      fCount.className   = 'px-2.5 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800';
      fCount.textContent = `All ${total} shown`;
    } else {
      fCount.className   = 'px-2.5 py-1 rounded-md text-xs font-medium bg-orange-100 text-orange-800';
      fCount.textContent = `${shown} / ${total} shown`;
    }
    fClear.classList.toggle('hidden', !anyFilter);
  }
  fVuln.onchange = applyFilters;
  fAsr.onchange  = applyFilters;
  fFunc.onchange = applyFilters;
  applyFilters();

  // Clear filters button (improvement 3)
  fClear.onclick = () => {
    fVuln.value   = '';
    fAsr.checked  = false;
    fFunc.checked = false;
    fSort.value   = 'default';
    applySort();
    applyFilters();
  };

  // Sort dropdown (improvement 4)
  function applySort() {
    const mode = fSort.value;
    const cards = Array.from(document.querySelectorAll('[data-card]'));
    const container = cards[0] && cards[0].parentNode;
    if (!container) return;

    function key(card) {
      const idx = parseInt(card.dataset.index, 10);
      const r = records[idx] || {};
      switch (mode) {
        case 'vuln': return [r.vuln_type || '￿', idx];
        case 'asr':  return [-(r.asr_pre || 0), idx];
        case 'deg':  return [-(r.func_degradation_injected == null
                                 ? -Infinity : r.func_degradation_injected), idx];
        case 'conf': return [r.confidence == null ? Infinity : r.confidence, idx];
        default:     return [idx];
      }
    }

    const sorted = cards.slice().sort((a, b) => {
      const ka = key(a), kb = key(b);
      for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
        const va = ka[i], vb = kb[i];
        if (va < vb) return -1;
        if (va > vb) return  1;
      }
      return 0;
    });

    // Brief fade-out → reorder → fade-in (Tailwind transition utilities)
    container.classList.add('transition-opacity', 'duration-150', 'opacity-50');
    requestAnimationFrame(() => {
      sorted.forEach(c => container.appendChild(c));   // moves nodes in place
      requestAnimationFrame(() => container.classList.remove('opacity-50'));
    });
  }
  fSort.onchange = () => { applySort(); applyFilters(); };

  // Export filtered results to JSON (improvement 8)
  fExport.onclick = () => {
    // Use data-index (stable per-card, set in improvement 4) for exact 1:1
    // mapping with what the user sees — avoids vuln_type collision issues
    // when multiple records share a vuln_type.
    const visible = Array.from(document.querySelectorAll('[data-card]:not([hidden])'))
      .map(c => records[parseInt(c.dataset.index, 10)])
      .filter(Boolean);

    // Shallow-copy all top-level keys (timestamp, skills, totals, rates, by_*),
    // then override findings_detail with the filtered subset and add metadata.
    // Note: the top-level aggregate rates and by_vuln_type/by_difficulty are
    // still computed over the FULL dataset, not the filtered subset. The
    // `filtered: true` marker makes that explicit.
    const payload = Object.assign({}, data);
    payload.filtered        = true;
    payload.filtered_count  = visible.length;
    payload.findings_detail = visible;

    const ts = (data.timestamp || new Date().toISOString())
      .replace(/[:T]/g, '-').slice(0, 19);
    const filename = `sse_filtered_${ts}.json`;

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Clickable metric bars → toggle filter checkboxes (improvement 2)
  document.querySelectorAll('[data-filter-trigger]').forEach(el => {
    el.addEventListener('click', () => {
      const k = el.dataset.filterTrigger;
      if (k === 'asr')  fAsr.checked  = true;
      if (k === 'func') fFunc.checked = true;
      applyFilters();
      // Scroll the first matching card into view so the user sees the effect
      const firstCard = document.querySelector('[data-card]:not([hidden])');
      if (firstCard) {
        firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Sticky header (~72px) overlaps the card top after scrollIntoView;
        // wait for the smooth scroll to finish, then nudge upward.
        setTimeout(() => window.scrollBy(0, -72), 300);
      }
    });
  });

  // Third-party comparison summary badges → click-to-filter rows. N INDEPENDENT
  // filter groups sharing one grid, EXCLUSIVE with each other (picking one
  // clears every other — they're different comparisons, see
  // renderPairFilterChips() above): 'engine' = overall/all-active-engines
  // (own 'failed' case: data-tp-failed instead of a status value), 'ssh'/'snyk'/
  // 'skillspector'/'cisco' = Blue vs that ONE engine. Click the active chip again to clear.
  const TP_FILTER_GROUPS = {
    engine:       { btnSel: '[data-tp-filter]',              btnData: 'tpFilter',              ring: 'ring-blue-400',
                    match: (row, key) => key === 'failed' ? row.dataset.tpFailed === 'true' : row.dataset.tpStatus === key },
    ssh:          { btnSel: '[data-tp-ssh-filter]',          btnData: 'tpSshFilter',            ring: 'ring-purple-400',
                    match: (row, key) => row.dataset.tpSshStatus === key },
    snyk:         { btnSel: '[data-tp-snyk-filter]',         btnData: 'tpSnykFilter',           ring: 'ring-sky-400',
                    match: (row, key) => row.dataset.tpSnykStatus === key },
    skillspector: { btnSel: '[data-tp-skillspector-filter]', btnData: 'tpSkillspectorFilter',   ring: 'ring-emerald-400',
                    match: (row, key) => row.dataset.tpSkillspectorStatus === key },
    cisco:        { btnSel: '[data-tp-cisco-filter]',        btnData: 'tpCiscoFilter',          ring: 'ring-indigo-400',
                    match: (row, key) => row.dataset.tpCiscoStatus === key },
  };
  let tpActiveFilter = null;   // {group: keyof TP_FILTER_GROUPS, key:string} | null
  function applyTpFilter() {
    document.querySelectorAll('[data-tp-row]').forEach(row => {
      const show = !tpActiveFilter || TP_FILTER_GROUPS[tpActiveFilter.group].match(row, tpActiveFilter.key);
      row.hidden = !show;
    });
    Object.entries(TP_FILTER_GROUPS).forEach(([gname, g]) => {
      document.querySelectorAll(g.btnSel).forEach(btn => {
        const active = !!tpActiveFilter && tpActiveFilter.group === gname && btn.dataset[g.btnData] === tpActiveFilter.key;
        btn.classList.toggle('ring-2', active);
        btn.classList.toggle(g.ring, active);
      });
    });
  }
  Object.entries(TP_FILTER_GROUPS).forEach(([gname, g]) => {
    document.querySelectorAll(g.btnSel).forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset[g.btnData];
        tpActiveFilter = (tpActiveFilter && tpActiveFilter.group === gname && tpActiveFilter.key === key)
          ? null : { group: gname, key };
        applyTpFilter();
      });
    });
  });
})();
