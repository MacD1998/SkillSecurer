#!/usr/bin/env bash
# todo_lib.sh - Core library for agent-todo skill

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${TODO_DB:-}" ]]; then
  WORKSPACE_DIR="${SCRIPT_DIR}/../.."
  TODO_DB="${WORKSPACE_DIR}/TODO.md"
fi

TODO_HEADER='| id | title | task_type | owner | requester | source | status | deadline | next_action | success_criteria | created_at | updated_at | last_attempt_at | completed_at | result | tags |'
TODO_SEPARATOR='|----|-------|-----------|-------|-----------|--------|--------|----------|-------------|------------------|------------|------------|-----------------|--------------|--------|------|'

generate_uuid() {
  if command -v uuidgen &>/dev/null; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  else
    printf '%s-%s-%s-%s-%s\n' \
      "$(openssl rand -hex 4)" \
      "$(openssl rand -hex 2)" \
      "$(openssl rand -hex 2)" \
      "$(openssl rand -hex 2)" \
      "$(openssl rand -hex 12)"
  fi
}

now_iso() {
  date '+%Y-%m-%dT%H:%M:%S%z' | sed 's/\([0-9]\{2\}\)\([0-9]\{2\}\)$/\1:\2/'
}

deadline_to_timestamp() {
  local deadline="$1"
  [[ -z "$deadline" ]] && echo 0 && return
  date -d "${deadline}" '+%s' 2>/dev/null || date -j -f '%Y-%m-%dT%H:%M:%S%z' "${deadline}" '+%s' 2>/dev/null || echo 0
}

hours_until_deadline() {
  local deadline="$1"
  local now_ts deadline_ts
  now_ts=$(date '+%s')
  deadline_ts=$(deadline_to_timestamp "$deadline")
  if [[ $deadline_ts -le 0 ]]; then echo 999; return; fi
  echo $(( (deadline_ts - now_ts) / 3600 ))
}

escape_cell() {
  local val="${1:-}"
  val="${val//$'\n'/<br>}"
  val="${val//|/\\|}"
  echo "$val"
}

unescape_cell() {
  local val="${1:-}"
  val="${val//<br>/$'\n'}"
  val="${val//\\|/|}"
  echo "$val"
}

init_db() {
  if [[ ! -f "$TODO_DB" ]]; then
    cat > "$TODO_DB" <<EOF
# agent-todo Database

<!-- Last updated: never -->

## TODOs

${TODO_HEADER}
${TODO_SEPARATOR}
EOF
    return
  fi

  ensure_schema
}

ensure_schema() {
  local header
  header=$(grep '^| id |' "$TODO_DB" 2>/dev/null || true)
  if [[ "$header" == "$TODO_HEADER" ]]; then
    return
  fi

  migrate_legacy_db
}

migrate_legacy_db() {
  local tmp ts
  tmp="${TODO_DB}.tmp"
  ts=$(now_iso)

  {
    echo '# agent-todo Database'
    echo
    echo "<!-- Last updated: ${ts} -->"
    echo
    echo '## TODOs'
    echo
    echo "$TODO_HEADER"
    echo "$TODO_SEPARATOR"

    awk -F'|' '
      NR <= 4 { next }
      !/^\|/ { next }
      /^\|[- ]+\|/ { next }
      {
        for (i=1; i<=NF; i++) {
          gsub(/^[ \t]+|[ \t]+$/, "", $i)
        }
        if ($2 == "id" || $2 == "") next
        id = $2
        title = $3
        deadline = $4
        owner = $5
        requester = $6
        source = $7
        status = $8
        created_at = $9
        updated_at = $10
        completed_at = $11
        notes = $12
        tags = $13

        if (status == "overdue") {
          status = "pending"
        }

        task_type = "general"
        next_action = notes
        success_criteria = "Mark done and report back to source"
        last_attempt_at = ""
        result = ""

        printf "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n", \
          id, title, task_type, owner, requester, source, status, deadline, next_action, success_criteria, created_at, updated_at, last_attempt_at, completed_at, result, tags
      }
    ' "$TODO_DB"
  } > "$tmp"

  mv "$tmp" "$TODO_DB"
}

touch_db() {
  local ts
  ts=$(now_iso)
  sed -i "s#<!-- Last updated: .*#<!-- Last updated: ${ts} -->#" "$TODO_DB"
}

get_field() {
  local id="$1"
  local col_name="$2"

  awk -F'|' -v id="$id" -v col="$col_name" '
    BEGIN { col_idx = 0 }
    /^\| *id *\|/ {
      for (i = 1; i <= NF; i++) {
        gsub(/^[ \t]+|[ \t]+$/, "", $i)
        if ($i == col) { col_idx = i; break }
      }
      next
    }
    !/^\|/ || /^\|[- ]+\|/ { next }
    {
      for (i = 1; i <= NF; i++) {
        gsub(/^[ \t]+|[ \t]+$/, "", $i)
      }
      if ($2 == id && col_idx > 0) {
        print $col_idx
        exit
      }
    }
  ' "$TODO_DB"
}

replace_row() {
  local id="$1"
  local new_row="$2"

  awk -F'|' -v id="$id" -v row="$new_row" '
    !/^\|/ || /^\|[- ]+\|/ { print; next }
    {
      raw = $0
      for (i = 1; i <= NF; i++) {
        gsub(/^[ \t]+|[ \t]+$/, "", $i)
      }
      if ($2 == id) {
        print row
      } else {
        print raw
      }
    }
  ' "$TODO_DB" > "${TODO_DB}.tmp"

  mv "${TODO_DB}.tmp" "$TODO_DB"
  touch_db
}

build_row() {
  local id="$1"
  local title="$2"
  local task_type="$3"
  local owner="$4"
  local requester="$5"
  local source="$6"
  local status="$7"
  local deadline="$8"
  local next_action="$9"
  local success_criteria="${10}"
  local created_at="${11}"
  local updated_at="${12}"
  local last_attempt_at="${13}"
  local completed_at="${14}"
  local result="${15}"
  local tags="${16}"

  printf '| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' \
    "$(escape_cell "$id")" \
    "$(escape_cell "$title")" \
    "$(escape_cell "$task_type")" \
    "$(escape_cell "$owner")" \
    "$(escape_cell "$requester")" \
    "$(escape_cell "$source")" \
    "$(escape_cell "$status")" \
    "$(escape_cell "$deadline")" \
    "$(escape_cell "$next_action")" \
    "$(escape_cell "$success_criteria")" \
    "$(escape_cell "$created_at")" \
    "$(escape_cell "$updated_at")" \
    "$(escape_cell "$last_attempt_at")" \
    "$(escape_cell "$completed_at")" \
    "$(escape_cell "$result")" \
    "$(escape_cell "$tags")"
}

find_rows() {
  awk 'NR > 6 && /^\|/ { print }' "$TODO_DB"
}

format_status() {
  case "$1" in
    pending) echo '⏳ pending' ;;
    running) echo '🏃 running' ;;
    blocked) echo '🧱 blocked' ;;
    done) echo '✅ done' ;;
    cancelled) echo '❌ cancelled' ;;
    *) echo "$1" ;;
  esac
}
