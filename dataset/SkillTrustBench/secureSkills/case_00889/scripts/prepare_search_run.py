#!/usr/bin/env python3
import json
import re
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE = SKILL_ROOT / 'data/profiles/sample-software-engineer-profile.md'
RUNS_DIR = SKILL_ROOT / 'data/search-runs'


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'search'


def extract_nested_list(lines, section_heading, subsection_label):
    values = []
    in_section = False
    in_subsection = False
    for line in lines:
        if line.startswith('## '):
            in_section = (line.strip() == section_heading)
            in_subsection = False
            continue
        if not in_section:
            continue
        stripped = line.rstrip()
        if stripped.strip().startswith(f'- {subsection_label}:'):
            in_subsection = True
            continue
        if in_subsection:
            if stripped.strip().startswith('- ') and not stripped.startswith('  - '):
                break
            if stripped.startswith('  - '):
                values.append(stripped.strip()[2:].strip())
    return values


def extract_section_bullets(lines, section_heading):
    values = []
    in_section = False
    for line in lines:
        if line.startswith('## '):
            in_section = (line.strip() == section_heading)
            continue
        if in_section and line.strip().startswith('- '):
            values.append(line.strip()[2:].strip())
    return values


def main():
    if not PROFILE.exists():
        raise SystemExit(f'Profile not found: {PROFILE}')

    content = PROFILE.read_text()
    lines = content.splitlines()

    desired_roles = extract_nested_list(lines, '## Target Direction', 'Desired roles')
    target_companies = extract_section_bullets(lines, '## Target Companies')
    preferred_locations = extract_nested_list(lines, '## Preferences', 'Preferred locations')
    work_modes = extract_nested_list(lines, '## Preferences', 'Work modes')
    primary_role = desired_roles[0] if desired_roles else 'job-search'
    now = datetime.now().astimezone()
    run_id = f"{now.date().isoformat()}-{slugify(primary_role)}"

    run = {
        'runId': run_id,
        'createdAt': now.isoformat(),
        'backend': 'jobspy-local-adapter',
        'profilePath': str(PROFILE.relative_to(SKILL_ROOT)),
        'desiredRoles': desired_roles,
        'targetCompanies': target_companies,
        'locations': preferred_locations,
        'workModes': work_modes,
        'freshnessWindow': '30d',
        'resultCount': 0,
        'notes': 'Prepared from self-contained skill profile.'
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f'{run_id}.json'
    out.write_text(json.dumps(run, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
