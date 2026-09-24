# Run Notes

## Current execution model

The skill currently operates through the skill-local project pipeline:

1. `skills/job-search-skill/scripts/prepare_search_run.py`
2. `skills/job-search-skill/scripts/search_backend_jobspy.py`
3. `skills/job-search-skill/scripts/normalize_jobs.py`
4. `skills/job-search-skill/scripts/render_search_summary.py`

## Environment

The project is now managed with `uv`.

Typical setup from project root:

```bash
uv sync
source .venv/bin/activate
```

## Backend

The backend is currently a local JobSpy-backed adapter.

This keeps the project fast to iterate on while preserving a clean boundary between:

- agent-facing skill behavior
- project-owned workflow
- backend search execution

## Outputs to check

After a run, inspect:

- `data/search-runs/*.json`
- `data/search-runs/*.md`
- `data/raw/*.json`
- `data/jobs/*.json`

## Current limitations

Known current limitations:

- source noise and regional failures may occur
- ZipRecruiter may fail in EU contexts
- deduplication is not yet strong
- work mode normalization still needs improvement
