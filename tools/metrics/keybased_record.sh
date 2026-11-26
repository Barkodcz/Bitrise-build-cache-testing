#!/usr/bin/env bash
# tools/metrics/keybased_record.sh record-restore|record-save <name> <key> [<paths>]  (spec §8.2)
#
# Called right after a restore-cache / save-cache step to capture its outcome into a metrics
# fragment: $BITRISE_CACHE_HIT (exact|partial|false) after restore, and an estimated archive size
# (sum of the cached paths' on-disk size) plus the save/restore timer value, merged later by
# merge_fragments.py into the final metrics JSON's `key_based` array.
set -euo pipefail

action="${1:?usage: keybased_record.sh record-restore|record-save <name> <key> [<paths>]}"
name="${2:?}"
key="${3:?}"
paths="${4:-}"

: "${SHOWCASE_METRICS_DIR:?}"
: "${SHOWCASE_SCENARIO_ID:?}"
: "${SHOWCASE_PHASE:?}"

frag_dir="$SHOWCASE_METRICS_DIR/.fragments/${SHOWCASE_SCENARIO_ID}__${SHOWCASE_PHASE}"
mkdir -p "$frag_dir"
frag_file="$frag_dir/keybased__${name}.json"

size_of_paths() {
  local total=0
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    expanded="${p/#\~/$HOME}"
    if [ -e "$expanded" ]; then
      # `du` on a large Go/Gradle cache dir can print permission-denied warnings to stderr for a
      # few unreadable files and exit non-zero even though it still reported a (partial) total —
      # under `set -e`/`pipefail` that non-zero exit was silently zeroing this metric out entirely
      # (verified 2026-11-26: a real report_go run showed archive_bytes=0 for both go caches despite
      # a confirmed non-empty, successfully-saved cache). `|| true` on `du` itself (not just the
      # pipe) keeps whatever partial total it managed to print.
      sz=$( (du -sk "$expanded" 2>/dev/null || true) | awk '{print $1}' )
      total=$((total + ${sz:-0} * 1024))
    fi
  done <<< "$paths"
  echo "$total"
}

case "$action" in
  record-restore)
    hit="${BITRISE_CACHE_HIT:-false}"
    python3 -c "
import json
d = {}
try:
    d = json.load(open('$frag_file'))
except FileNotFoundError:
    pass
d.update({'name': '$name', 'key': '''$key''', 'restore_hit': '$hit'})
json.dump(d, open('$frag_file', 'w'))
"
    echo "keybased_record: restore name=$name hit=$hit"
    ;;
  record-save)
    bytes="$(size_of_paths)"
    python3 -c "
import json
d = {}
try:
    d = json.load(open('$frag_file'))
except FileNotFoundError:
    pass
d.update({'name': '$name', 'key': '''$key''', 'archive_bytes': $bytes, 'saved': True})
json.dump(d, open('$frag_file', 'w'))
"
    echo "keybased_record: save name=$name bytes=$bytes"
    ;;
  *)
    echo "unknown action: $action" >&2
    exit 1
    ;;
esac
