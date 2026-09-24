#!/usr/bin/env bash
set -euo pipefail

echo "This legacy restore skill has been superseded by the self-contained backup bundle format." >&2
echo "Please extract the backup tar.gz and run: bash <bundle-dir>/restore.sh" >&2
exit 1
