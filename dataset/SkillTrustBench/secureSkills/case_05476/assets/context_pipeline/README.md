# Context Pipeline v1 (retrieval + compression)

Portable spec for agents:

1) Always include `always_on.md`.
2) Route message → task_type using `router.yml`.
3) Retrieve snippets from memory according to router policy; emit Retrieval Bundle JSON.
4) Compress Retrieval Bundle → Context Pack JSON using `compressor_prompt.txt`.
5) Lint Context Pack; if it fails, fall back to raw snippets.
6) Feed Always-on policy + Context Pack (+ optional raw snippets) + user message to the reasoning model.

Files:
- `always_on.md` — tiny always-on policy + topic catalog (template).
- `router.yml` — deterministic task router + retrieval caps.
- `compressor_prompt.txt` — prompt for cheap compressor model.
- `schemas/retrieval_bundle.schema.json` — JSON Schema for retrieval bundle.
- `schemas/context_pack.schema.json` — JSON Schema for context pack.
- `tests/golden.json` — starter golden tests.

Version: v1.0
