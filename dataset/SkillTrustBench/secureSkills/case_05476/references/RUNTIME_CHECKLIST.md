# Runtime Evidence Checklist — dr-context-pipeline

Agents **must** follow this checklist on every task once the context pipeline is installed.

1. **Retrieval Bundle JSON**
   - Load `memory/always_on.md`.
   - Route + retrieve according to `context_pipeline/router.yml` caps.
   - Emit the Retrieval Bundle object (matching `references/schemas/retrieval_bundle.schema.json`) in the transcript.
   - Include `snippet_id`, `path`, `start_line`, `end_line`, `citation`, and `text` for every snippet.
   - List any `dropped` entries with reasons.

2. **Context Pack JSON**
   - Compress using `context_pipeline/compressor_prompt.txt`.
   - Emit the Context Pack object (matching `references/schemas/context_pack.schema.json`).
   - `sources` arrays **must** be snippet IDs (e.g., `["S1","S3"]`).
   - If lint fails, explicitly state `CONTEXT PACK LINT FAILED` and paste the lint error.

3. **Snippet Summary + Pass-through**
   - Provide a short bullet list of which snippets (by ID) you are passing into the reasoning step and why.
   - Note any snippets intentionally excluded via `exclude_as_irrelevant`.

4. **Reasoning Output**
   - Only after the artifacts above, proceed with the user-facing answer.
   - Reference snippet IDs in-line (e.g., `Source: S2`).

5. **Failure Contract**
   - If any step above cannot be completed, reply exactly `NOT EXECUTED: <reason>` and stop. Do **not** invent bundles or packs.

This checklist is non-optional. If the user issues a casual instruction like “go for it,” you still must emit the Retrieval Bundle + Context Pack or return `NOT EXECUTED`.
