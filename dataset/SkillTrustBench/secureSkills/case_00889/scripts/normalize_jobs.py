#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = SKILL_ROOT / 'data/raw'
JOBS_DIR = SKILL_ROOT / 'data/jobs'
RUNS_DIR = SKILL_ROOT / 'data/search-runs'


def normalize_record(raw, run_id):
    now = datetime.now().astimezone().isoformat()
    title = raw.get('title') or raw.get('job_title') or 'Unknown Title'
    company = raw.get('company') or raw.get('company_name') or 'Unknown Company'
    location = raw.get('location') or raw.get('job_location') or 'Unknown Location'
    url = raw.get('url') or raw.get('job_url') or raw.get('job_url_direct') or ''
    source = raw.get('source') or raw.get('site') or raw.get('site_name') or 'unknown'
    return {
        'id': f"{run_id}-{company}-{title}".lower().replace(' ', '-').replace('/', '-'),
        'title': title,
        'company': company,
        'location': location,
        'workMode': raw.get('workMode') or ('remote' if raw.get('is_remote') else None),
        'source': source,
        'url': url,
        'postedDate': raw.get('postedDate') or raw.get('date_posted'),
        'discoveredAt': now,
        'salary': raw.get('salary') or raw.get('min_amount'),
        'summary': raw.get('summary') or raw.get('description') or raw.get('job_summary'),
        'fitNote': raw.get('fitNote') or '',
        'status': 'new',
        'runId': run_id,
    }


def main():
    raw_files = sorted(RAW_DIR.glob('*.json'))
    if not raw_files:
        raise SystemExit('No raw backend outputs found. Run search_backend_jobspy.py first.')
    latest_raw = raw_files[-1]
    payload = json.loads(latest_raw.read_text())
    run_id = payload['runId']

    normalized = []
    for entry in payload.get('rawResults', []):
        for item in entry.get('results', []):
            normalized.append(normalize_record(item, run_id))

    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    out = JOBS_DIR / f'{run_id}.json'
    out.write_text(json.dumps(normalized, indent=2) + '\n')

    run_path = RUNS_DIR / f'{run_id}.json'
    if run_path.exists():
        run = json.loads(run_path.read_text())
        run['resultCount'] = len(normalized)
        run_path.write_text(json.dumps(run, indent=2) + '\n')

    print(out)


if __name__ == '__main__':
    main()
