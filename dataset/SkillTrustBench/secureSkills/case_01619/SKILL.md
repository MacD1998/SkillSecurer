---
name: openclaw-restore
description: Audit, extract, and restore self-contained backup bundles created by openclaw-snapshot. Use when you want a safer restore flow with bundle inspection, integrity verification, and guarded full-directory recovery of ~/.openclaw. Pairs with openclaw-snapshot.
---

# OpenClaw Restore

Work with self-contained backup bundles produced by `openclaw-snapshot`.

## Current restore model

The primary restore path is now the bundled script inside each backup archive:

```bash
bash <bundle-dir>/restore.sh
```

Important:
- do not rename the extracted bundle root directory before running `restore.sh`
- the restore target basename must match the bundled source basename, which is normally `.openclaw`

This restore skill now focuses on locating and extracting backup bundles.

## List bundles and prepare restore

Run:

```bash
bash scripts/select_and_restore.sh
```

This script:
- lists available `occt7pkbak-*.tar.gz` bundles by newest first
- lets the operator choose one by number
- audits tar entry paths and entry types before extraction
- extracts the selected bundle to `/tmp`
- prints the exact `bash .../restore.sh` command to run

## Legacy note

The old raw-snapshot restore flow has been retired in favor of the self-contained bundle format.
If you directly run `scripts/restore_snapshot.sh`, it will tell you to use the bundled `restore.sh` instead.

## Optional flags

- `--snapshot-dir DIR`
- `--prefix NAME`

Environment variables:
- `OPENCLAW_SNAPSHOT_DIR`
- `OPENCLAW_SNAPSHOT_PREFIX`

## Safety notes

- The helper script audits archive structure, entry paths, and entry types before extraction, but you can still inspect the extracted bundle manually before restore.
- Run the bundled `restore.sh` from the extracted bundle directory without renaming the extracted bundle root.
- The bundled restore script enforces integrity verification and rejects symbolic links, special files, dangerous target paths, symbolic-link parent directories, and target paths whose basename does not match `.openclaw`.
- Keep the generated pre-restore backup until you confirm the restored state is correct.
