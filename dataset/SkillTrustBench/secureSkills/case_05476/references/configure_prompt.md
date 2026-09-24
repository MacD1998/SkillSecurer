# Activation prompt (copy/paste fallback)

Preferred activation phrase:
`Apply dr-context-pipeline as default behavior`

If you need a longer prompt that bakes in the evidence contract, use this:

---
Use **DR Context Pipeline** as your default context-loading and memory protocol.

**Spec files** live under `context_pipeline/` (installed via `skills/dr-context-pipeline/scripts/install_pipeline.py`).

For every user message you must:
1. Load `memory/always_on.md` verbatim.
2. Route deterministically using `context_pipeline/router.yml` (task_type + derived queries + caps).
3. Retrieve memory snippets and build a Retrieval Bundle JSON that matches `context_pipeline/schemas/retrieval_bundle.schema.json`. Include snippet IDs (S1..Sn), citations, and dropped snippets.
4. Compress to a Context Pack JSON using `context_pipeline/compressor_prompt.txt` and `context_pipeline/schemas/context_pack.schema.json`. `sources` arrays must list snippet IDs only.
5. Lint the Context Pack. If lint fails, explicitly say `CONTEXT PACK LINT FAILED`, include the error, and fall back to the raw snippets.
6. Emit (in this order) → Retrieval Bundle JSON, Context Pack JSON (or lint failure), snippet summary, then the user-facing reasoning.
7. If any step cannot be completed exactly, reply `NOT EXECUTED: <reason>`.

**Never** claim you performed a step without pasting the artifact. Casual prompts do not waive this requirement.

To install/refresh the files and validate the setup, run:
```
export WORKSPACE=${WORKSPACE:-~/.openclaw/workspace}
cd "$WORKSPACE"
clawhub install dr-context-pipeline --version X.Y.Z --dir skills
python3 ./skills/dr-context-pipeline/scripts/install_pipeline.py --target "$WORKSPACE/context_pipeline"
ls -1 "$WORKSPACE/context_pipeline"
git -C "$WORKSPACE" diff -U20 AGENTS.md | cat
python3 ./skills/dr-context-pipeline/scripts/validate_pipeline.py --context-root "$WORKSPACE/context_pipeline"
python3 ./skills/dr-context-pipeline/scripts/memory_watchdog.py --freshness-minutes 240 --min-bytes 200
git -C "$WORKSPACE" status -sb context_pipeline AGENTS.md
echo "CONTEXT PIPELINE APPLY COMPLETE"
```
(Include the command outputs in the confirmation.)
---
