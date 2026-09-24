#!/usr/bin/env bash
# Log wiki changes to local changelog
# Usage: log-change.sh <agent_name> <module> <action_summary>
set -euo pipefail
CHANGELOG_FILE="$(dirname "$0")/../changelog.md"
AGENT="${1:?Usage: log-change.sh <agent> <module> <summary>}"
MODULE="${2:?Missing module}"
SUMMARY="${3:?Missing summary}"
TIMESTAMP="$(date -u +'%Y-%m-%d %H:%M UTC')"
if [ ! -f "$CHANGELOG_FILE" ]; then
  printf '# Wiki Changelog

| Time | Agent | Module | Change |
|------|-------|--------|--------|
' > "$CHANGELOG_FILE"
fi
echo "| ${TIMESTAMP} | ${AGENT} | ${MODULE} | ${SUMMARY} |" >> "$CHANGELOG_FILE"
echo "Done: [${TIMESTAMP}] ${AGENT} -> ${MODULE}: ${SUMMARY}"
