#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SNAPSHOT_DIR="/home/bookerwei/nfsserver/nfsShare/openclawbackup/occt7pkbackup"
SNAPSHOT_DIR="${OPENCLAW_SNAPSHOT_DIR:-$DEFAULT_SNAPSHOT_DIR}"
SNAPSHOT_PREFIX="${OPENCLAW_SNAPSHOT_PREFIX:-occt7pkbak}"
PACKAGE_MANIFEST_NAME="manifest.txt"
PACKAGE_CHECKSUM_NAME="SHA256SUMS"
RESTORE_SCRIPT_NAME="restore.sh"

usage() {
  cat <<'EOF'
Usage: select_and_restore.sh [--snapshot-dir DIR] [--prefix NAME]

List available backup bundles, let the operator choose one by number, audit the tar contents,
extract it to a temp location, then print the exact restore command to run.
EOF
}

require_value() {
  local option="$1"
  local value="${2-}"
  if [[ -z "$value" ]]; then
    echo "Missing value for $option" >&2
    usage >&2
    exit 1
  fi
}

audit_bundle_archive() {
  local archive_path="$1"
  local expected_prefix="$2"
  mapfile -t entries < <(tar -tvzf "$archive_path")
  if (( ${#entries[@]} == 0 )); then
    echo "Archive is empty: $archive_path" >&2
    exit 1
  fi

  local bundle_root=""
  local line type path rel rest first_component
  for line in "${entries[@]}"; do
    type="${line:0:1}"
    path="$(printf '%s\n' "$line" | awk '{for (i=6; i<=NF; i++) printf (i==6 ? "%s" : " %s"), $i; printf "\n"}')"
    if [[ -z "$path" ]]; then
      echo "Archive contains malformed listing entry" >&2
      exit 1
    fi
    if [[ "$path" == /* ]] || [[ "$path" == *".."* ]]; then
      echo "Archive contains unsafe path: $path" >&2
      exit 1
    fi
    case "$type" in
      d|-)
        ;;
      *)
        echo "Archive contains unsupported entry type: $path" >&2
        exit 1
        ;;
    esac

    rel="${path#./}"
    first_component="${rel%%/*}"
    if [[ -z "$bundle_root" ]]; then
      bundle_root="$first_component"
      if [[ ! "$bundle_root" =~ ^${expected_prefix}-[0-9]{8}-[0-9]{6}/?$ && ! "$bundle_root" =~ ^${expected_prefix}-[0-9]{8}-[0-9]{6}$ ]]; then
        echo "Archive root does not match expected bundle naming: $bundle_root" >&2
        exit 1
      fi
    elif [[ "$first_component" != "$bundle_root" ]]; then
      echo "Archive contains multiple top-level roots" >&2
      exit 1
    fi

    if [[ "$rel" == "$bundle_root" || "$rel" == "$bundle_root/" ]]; then
      if [[ "$type" != d ]]; then
        echo "Archive root must be a directory: $path" >&2
        exit 1
      fi
      continue
    fi
    rest="${rel#${bundle_root}/}"
    case "$rest" in
      "$PACKAGE_MANIFEST_NAME"|"$PACKAGE_CHECKSUM_NAME"|"$RESTORE_SCRIPT_NAME")
        if [[ "$type" != - ]]; then
          echo "Bundle metadata entry must be a regular file: $path" >&2
          exit 1
        fi
        ;;
      .openclaw)
        if [[ "$type" != d ]]; then
          echo "Bundled .openclaw root must be a directory: $path" >&2
          exit 1
        fi
        ;;
      .openclaw/*)
        if [[ "$type" != d && "$type" != - ]]; then
          echo "Bundled .openclaw contains unsupported entry type: $path" >&2
          exit 1
        fi
        ;;
      *)
        echo "Archive contains unexpected entry: $path" >&2
        exit 1
        ;;
    esac
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot-dir)
      require_value "$1" "${2-}"
      SNAPSHOT_DIR="$2"
      shift 2
      ;;
    --prefix)
      require_value "$1" "${2-}"
      SNAPSHOT_PREFIX="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! [[ "$SNAPSHOT_PREFIX" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "--prefix may contain only letters, digits, dot, underscore, and hyphen" >&2
  exit 1
fi

mapfile -t bundles < <(find "$SNAPSHOT_DIR" -maxdepth 1 -type f -name "${SNAPSHOT_PREFIX}-*.tar.gz" | sort -r)
if (( ${#bundles[@]} == 0 )); then
  echo "No backup bundles found in: $SNAPSHOT_DIR" >&2
  exit 1
fi

printf 'Available backup bundles in %s\n\n' "$SNAPSHOT_DIR"
for i in "${!bundles[@]}"; do
  file="${bundles[$i]}"
  mtime="$(date -d "@$(stat -c %Y "$file")" '+%Y-%m-%d %H:%M:%S')"
  size="$(du -h "$file" | cut -f1)"
  printf '%2d) %s  [%s, %s]\n' "$((i + 1))" "$(basename "$file")" "$mtime" "$size"
done

printf '\nChoose bundle number to extract: '
if ! read -r choice; then
  echo "No selection received" >&2
  exit 1
fi
if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
  echo "Choice must be a number" >&2
  exit 1
fi

index=$((choice - 1))
if (( index < 0 || index >= ${#bundles[@]} )); then
  echo "Choice out of range" >&2
  exit 1
fi

selected="${bundles[$index]}"
audit_bundle_archive "$selected" "$SNAPSHOT_PREFIX"
extract_dir="$(mktemp -d /tmp/openclaw-restore-bundle.XXXXXX)"
tar -C "$extract_dir" -xzf "$selected"
bundle_root="$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$bundle_root" || ! -f "$bundle_root/$RESTORE_SCRIPT_NAME" || ! -f "$bundle_root/$PACKAGE_MANIFEST_NAME" || ! -f "$bundle_root/$PACKAGE_CHECKSUM_NAME" ]]; then
  echo "Extracted bundle is incomplete" >&2
  exit 1
fi
if [[ -L "$bundle_root" ]]; then
  echo "Refusing symbolic-link bundle root: $bundle_root" >&2
  exit 1
fi
if find "$bundle_root/.openclaw" -type l -print -quit | grep -q .; then
  echo "Refusing bundle with symbolic links in .openclaw" >&2
  exit 1
fi

printf 'Extracted to: %s\n' "$bundle_root"
printf 'Run this to restore:\n'
printf 'bash %q/%s\n' "$bundle_root" "$RESTORE_SCRIPT_NAME"
