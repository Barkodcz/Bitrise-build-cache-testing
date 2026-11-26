#!/usr/bin/env bash
# tools/metrics/timing.sh start|stop <name>   (spec §8.2)
#
# Named timers -> metrics fragments. Each call appends/updates a JSON fragment file under
# $SHOWCASE_METRICS_DIR/.fragments/<scenario>__<phase>/<name>.json with monotonic epoch timestamps.
# tools/metrics/merge_fragments.py later folds every fragment for a scenario+phase into the final
# metrics/<SCENARIO>__<phase>.json (spec §8.1 durations_s.*).
set -euo pipefail

action="${1:?usage: timing.sh start|stop <name>}"
name="${2:?usage: timing.sh start|stop <name>}"

: "${SHOWCASE_SCENARIO_ID:?SHOWCASE_SCENARIO_ID must be exported}"
: "${SHOWCASE_PHASE:?SHOWCASE_PHASE must be exported}"
: "${SHOWCASE_METRICS_DIR:?SHOWCASE_METRICS_DIR must be exported}"

frag_dir="$SHOWCASE_METRICS_DIR/.fragments/${SHOWCASE_SCENARIO_ID}__${SHOWCASE_PHASE}"
mkdir -p "$frag_dir"
frag_file="$frag_dir/${name}.json"
now="$(python3 -c 'import time; print(time.time())')"

case "$action" in
  start)
    python3 -c "import json; json.dump({'name': '$name', 'started_at': $now}, open('$frag_file', 'w'))"
    ;;
  stop)
    if [ ! -f "$frag_file" ]; then
      echo "timing.sh stop: no start recorded for '$name', recording duration 0" >&2
      python3 -c "import json; json.dump({'name': '$name', 'started_at': $now, 'duration_s': 0.0}, open('$frag_file', 'w'))"
    else
      python3 - "$frag_file" "$now" <<'PY'
import json, sys
frag_file, now = sys.argv[1], float(sys.argv[2])
d = json.load(open(frag_file))
d["stopped_at"] = now
d["duration_s"] = round(now - d["started_at"], 3)
json.dump(d, open(frag_file, "w"))
PY
    fi
    ;;
  *)
    echo "unknown action: $action (expected start|stop)" >&2
    exit 1
    ;;
esac
