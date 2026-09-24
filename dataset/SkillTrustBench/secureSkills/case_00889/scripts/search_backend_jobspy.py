#!/usr/bin/env python3
import json
from pathlib import Path

from jobspy import scrape_jobs

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = SKILL_ROOT / 'data/search-runs'
RAW_DIR = SKILL_ROOT / 'data/raw'
CONFIG_PATH = SKILL_ROOT / 'config/search-defaults.json'


def load_latest_run():
    run_files = sorted(RUNS_DIR.glob('*.json'))
    if not run_files:
        raise SystemExit('No search runs found. Run prepare_search_run.py first.')
    latest = run_files[-1]
    return json.loads(latest.read_text())


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit(f'Config not found: {CONFIG_PATH}')
    return json.loads(CONFIG_PATH.read_text())


def build_requests(run, config):
    requests = []
    roles = run.get('desiredRoles', [])[:2]
    locations = run.get('locations', [])[:2] or ['Remote']
    work_modes = set(v.lower() for v in run.get('workModes', []))
    target_companies = run.get('targetCompanies', [])[:3]

    for role in roles:
        for location in locations:
            requests.append({
                'search_term': role,
                'location': location,
                'site_name': config['siteNames'],
                'results_wanted': config['resultsWanted'],
                'hours_old': config['freshnessHours'],
                'is_remote': 'remote' in work_modes,
                'easy_apply': config['easyApply'],
                'linkedin_fetch_description': config['linkedinFetchDescription'],
                'country_indeed': config['defaultCountryIndeed'],
                'verbose': config['verbose'],
            })
        for company in target_companies:
            requests.append({
                'search_term': f'{role} {company}',
                'location': locations[0],
                'site_name': config['siteNames'],
                'results_wanted': 8,
                'hours_old': config['freshnessHours'],
                'is_remote': 'remote' in work_modes,
                'easy_apply': config['easyApply'],
                'linkedin_fetch_description': False,
                'country_indeed': config['defaultCountryIndeed'],
                'verbose': config['verbose'],
            })
    return requests


def dataframe_to_records(df):
    if df is None:
        return []
    return json.loads(df.to_json(orient='records', date_format='iso'))


def live_execute(requests):
    payload = []
    failures = []
    for request in requests:
        try:
            df = scrape_jobs(**request)
            payload.append({
                'request': request,
                'mode': 'live',
                'results': dataframe_to_records(df),
            })
        except Exception as e:
            failures.append({'request': request, 'error': repr(e)})
            payload.append({
                'request': request,
                'mode': 'error',
                'error': repr(e),
                'results': [],
            })

    if not any(entry.get('mode') == 'live' and entry.get('results') for entry in payload):
        raise SystemExit(f'Live job search failed or returned no results for all requests: {failures}')

    return payload


def main():
    run = load_latest_run()
    config = load_config()
    run_id = run['runId']
    requests = build_requests(run, config)
    raw_results = live_execute(requests)

    raw_payload = {
        'runId': run_id,
        'backend': 'jobspy-local-adapter',
        'mode': 'live',
        'requests': requests,
        'rawResults': raw_results,
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f'{run_id}.json'
    out.write_text(json.dumps(raw_payload, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
