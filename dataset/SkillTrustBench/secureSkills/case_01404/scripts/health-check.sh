#!/bin/bash
# Memory system health check — verifies invariants before important operations
set -euo pipefail
MEMORY_DIR="/home/irtual/.openclaw/workspace/memory"
EXIT=0

echo "=== Memory Health Check ($(date '+%Y-%m-%d %H:%M')) ==="

# 1. Warm files: tags on line 2
echo ""
echo "🏷️  Tags on line 2 (WARM files):"
for f in "$MEMORY_DIR"/semantic/*.md "$MEMORY_DIR"/procedural/*.md; do
    [ -f "$f" ] || continue
    line2=$(sed -n '2p' "$f")
    fname=$(basename "$f")
    if echo "$line2" | grep -q "^#tags:"; then
        echo "   ✅ $fname"
    else
        echo "   ❌ $fname — missing #tags:"
        EXIT=1
    fi
done

# 2. Warm files: last_verified
echo ""
echo "📅 last_verified (WARM files):"
for f in "$MEMORY_DIR"/semantic/*.md "$MEMORY_DIR"/procedural/*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    if grep -q "^> last_verified:" "$f"; then
        lvd=$(grep "^> last_verified:" "$f" | head -1 | cut -d' ' -f3)
        lve=$(date -d "$lvd" +%s 2>/dev/null || echo 0)
        now=$(date +%s)
        days=$(( (now - lve) / 86400 ))
        if [ "$days" -lt 30 ]; then
            echo "   ✅ $fname ($days d)"
        else
            echo "   ⚠️  $fname ($days d — stale)"
        fi
    else
        echo "   ❌ $fname — missing last_verified"
        EXIT=1
    fi
done

# 3. Buffer size
echo ""
echo "📝 Buffer size:"
buf="$MEMORY_DIR/working-buffer.md"
if [ -f "$buf" ]; then
    lines=$(wc -l < "$buf")
    if [ "$lines" -le 80 ]; then
        echo "   ✅ $lines lines (limit: 80)"
    else
        echo "   ⚠️  $lines lines — exceeds 80 line limit"
        EXIT=1
    fi
else
    echo "   ✅ buffer not found"
fi

# 4. Open questions count
echo ""
echo "❓ Open Questions:"
mem="$MEMORY_DIR/MEMORY.md"
if [ -f "$mem" ]; then
    q_count=$(awk '/^## \ud83d\udd0d Open Questions/,0' "$mem" | grep -c "^[0-9]\." || true)
    if [ "$q_count" -le 5 ]; then
        echo "   ✅ $q_count questions (max: 5)"
    else
        echo "   ⚠️  $q_count questions — exceeds 5"
    fi
fi

# 5. Episodic today exists
echo ""
echo "📅 Today's episodic:"
today=$(date +%Y-%m-%d)
epi="$MEMORY_DIR/episodic/$today.md"
if [ -f "$epi" ]; then
    echo "   ✅ exists"
else
    echo "   ℹ️  not yet created (normal)"
fi

echo ""
if [ "$EXIT" -eq 0 ]; then
    echo "✅ All checks passed"
else
    echo "⚠️  Some checks failed — review above"
fi

exit $EXIT
