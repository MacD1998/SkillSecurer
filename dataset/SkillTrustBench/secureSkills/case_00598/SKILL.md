---
name: openclaw-snapshot
description: Create self-contained backup bundles for ~/.openclaw, including .openclaw/, manifest.txt, SHA256SUMS, and a bundled restore.sh for full-state recovery. Use before upgrades, migrations, risky config changes, or any time you want a restorable OpenClaw backup. Pairs with openclaw-restore.
---

# OpenClaw Snapshot

Create a self-contained tar.gz backup bundle for `~/.openclaw`.

## Quick use

Run:

```bash
bash scripts/create_snapshot.sh
```

Default behavior:
- source directory: `~/.openclaw`
- output directory: `/home/bookerwei/nfsserver/nfsShare/openclawbackup/occt7pkbackup`
- bundle filename format: `occt7pkbak-YYYYMMDD-HHMMSS.tar.gz`
- bundle contents:
  - `occt7pkbak-YYYYMMDD-HHMMSS/.openclaw/`
  - `occt7pkbak-YYYYMMDD-HHMMSS/restore.sh`
  - `occt7pkbak-YYYYMMDD-HHMMSS/manifest.txt`
  - `occt7pkbak-YYYYMMDD-HHMMSS/SHA256SUMS`
- retention: keep newest 5 bundles

## Restore flow

Extract the bundle, keep the extracted top-level directory name unchanged, then run:

```bash
bash occt7pkbak-YYYYMMDD-HHMMSS/restore.sh
```

The bundled restore script will:
- verify `SHA256SUMS` and does not allow skipping integrity verification
- validate `manifest.txt`
- require the restore target basename to match the bundled source basename, which is normally `.openclaw`
- reject symbolic links and special files in the bundled `.openclaw`
- refuse dangerous target paths and symbolic-link parent directories
- create a pre-restore backup of the current target by default
- replace the whole target directory with the bundled `.openclaw`

## Override behavior

Supported flags:
- `--out-dir DIR`
- `--source-dir DIR`
- `--keep N`
- `--prefix NAME`

Supported environment variables:
- `OPENCLAW_SNAPSHOT_DIR`
- `OPENCLAW_SOURCE_DIR`
- `OPENCLAW_SNAPSHOT_KEEP`

Priority order is: command-line flags > environment variables > defaults.

Notes:
- `--keep` must be `1` or greater
- `--prefix` may contain only letters, digits, dot, underscore, and hyphen
- use a stable prefix if you want bundle discovery tools to keep finding older bundles

## Safety notes

- Treat backup bundles as sensitive because they include the full OpenClaw state.
- Prefer writing to an existing backup location with enough free space.
- Use this skill before config edits, upgrades, migrations, large cleanup, or skill refactors.
- Backup bundle creation rejects symbolic links and special files inside the source tree.
- The bundled restore script is the primary restore path for this format.
