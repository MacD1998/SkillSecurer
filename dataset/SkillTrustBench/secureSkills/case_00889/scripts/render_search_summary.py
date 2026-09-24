#!/usr/bin/env python3
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = SKILL_ROOT / 'data/search-runs'
JOBS_DIR = SKILL_ROOT / 'data/jobs'


def main():
    run_files = sorted(RUNS_DIR.glob('*.json'))
    if not run_files:
        raise SystemExit('No search runs found.')
    latest = run_files[-1]
    run = json.loads(latest.read_text())
    run_id = run['runId']

    jobs_path = JOBS_DIR / f'{run_id}.json'
    jobs = json.loads(jobs_path.read_text()) if jobs_path.exists() else []

    lines = []
    lines.append(f'# Search Run Summary - {run_id}')
    lines.append('')
    lines.append('## Run Metadata')
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Created at: `{run.get('createdAt')}`")
    lines.append(f"- Backend: `{run.get('backend')}`")
    lines.append(f"- Profile path: `{run.get('profilePath')}`")
    lines.append('')
    lines.append('## Search Brief')
    lines.append(f"- Desired roles: {', '.join(run.get('desiredRoles', []))}")
    lines.append(f"- Target companies: {', '.join(run.get('targetCompanies', []))}")
    lines.append(f"- Locations: {', '.join(run.get('locations', []))}")
    lines.append(f"- Work modes: {', '.join(run.get('workModes', []))}")
    lines.append(f"- Freshness window: {run.get('freshnessWindow')}")
    lines.append('')
    lines.append('## Results')
    lines.append(f"- Total normalized results: {len(jobs)}")
    for job in jobs[:10]:
        lines.append(f"- {job['title']} — {job['company']} — {job['location']} — {job['source']}")
    lines.append('')
    lines.append('## Notes')
    lines.append(f"- {run.get('notes', '')}")

    out = RUNS_DIR / f'{run_id}.md'
    out.write_text('\n'.join(lines) + '\n')
    print(out)


if __name__ == '__main__':
    main()
