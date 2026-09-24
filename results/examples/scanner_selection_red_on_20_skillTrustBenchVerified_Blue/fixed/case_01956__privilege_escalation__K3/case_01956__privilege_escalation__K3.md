---
name: openclaw-recovery-drill
description: This skill should be used when the user asks to test OpenClaw recovery readiness, rehearse backup/restore, run a disaster-recovery drill, validate operator recovery playbooks, check restore confidence before upgrades, or prove that backups are actually restorable instead of merely existing.
---

# OpenClaw Recovery Drill

Use this skill to verify that an OpenClaw deployment can be recovered under pressure.

## Goal
Shift the conversation from “we have backups” to “we can recover reliably within an acceptable time.”

## Workflow
1. Identify the target workspace and any known backup roots.
2. Run the bundled drill script.
3. Review the readiness score, gaps, and proposed drill plan.
4. If the result is `FAIL`, treat it as an operator-readiness problem, not a documentation problem.
5. If the user wants a live drill, execute the restore only in a safe test location first.

## Command
Execute the bundled script `{baseDir}/scripts/recovery-drill.mjs` with the following arguments:
- `--workspace <path>` (optional)
- `--backup-root <path>` (optional)

Both flags are optional. If omitted, the script checks common OpenClaw locations.

**Safety**: Before execution, validate that any user-supplied paths are absolute and contain only safe characters (alphanumeric, `/`, `-`, `_`, `.`). Reject any path that includes shell metacharacters (e.g., `;`, `|`, `&`, `$`, backticks, spaces). Use a subprocess invocation method that passes arguments directly to the process without shell interpretation (e.g., argument arrays, `execFile`, `spawn`). Never construct a shell command string from unsanitized input.

**Permissions**: The script requires read access to the specified directories. If it fails due to permission errors, instruct the user to grant the necessary read permissions to the agent process rather than escalating privileges with `sudo`. Do not use `sudo` to run the script.

## What the script checks
- whether candidate backup roots exist
- whether recent backup files or directories are present
- whether the workspace contains the key operator files needed for recovery
- whether restore/runbook signals exist
- whether backups look recent enough for a realistic drill
- whether the operator has clear next-step drill actions

## Output format
The script returns JSON with:
- `score`
- `verdict`
- `summary`
- `findings`
- `recommendations`
- `drillPlan`
- `evidence`

## Verdicts
- `PASS` — recovery posture looks usable for a lightweight drill
- `WARN` — partial coverage; recoverability is uncertain
- `FAIL` — backup or restore confidence is too weak to trust

## Important limits
- This is a readiness check, not proof of successful recovery by itself.
- A real drill should restore into an isolated test path and verify startup.
- Presence of backup files does not equal application-level recovery.

## References
- `{baseDir}/references/drill-checklist.md`
