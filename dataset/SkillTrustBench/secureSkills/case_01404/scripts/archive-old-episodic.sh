#!/bin/bash
# Archive episodic files older than $1 days (default 30)
# Places archived files into archive/YYYY/MM/ structure
set -euo pipefail
MEMORY_DIR="/home/irtual/.openclaw/workspace/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"
RETENTION_DAYS="${1:-30}"
echo "=== Episodic Archival ($(date '+%Y-%m-%d %H:%M')) ==="
count=0
for file in "$MEMORY_DIR"/episodic/*.md; do
    [ -f "$file" ] || continue
    if [ "$(find "$file" -mtime +"$RETENTION_DAYS" -print 2>/dev/null)" ]; then
        fname=$(basename "$file")
        fdate="${fname:0:7}"  # YYYY-MM
        dest="$ARCHIVE_DIR/$fdate"
        mkdir -p "$dest"
        echo "  Archive: $fname → $fdate/"
        mv "$file" "$dest/"
        count=$((count + 1))
    fi
done
echo "✅ Archived: $count files (> ${RETENTION_DAYS} days old)"
echo "Done."
